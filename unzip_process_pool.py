import queue
import time
from collections import defaultdict
from enum import Enum
from multiprocessing import Process, Manager


class Prefix(Enum):
    PASSWORD_COLLISION = 'PC_'
    UNZIP = 'unzip_'


def _worker_loop(queue, result_queue):
    while True:
        item = queue.get()
        if item is None:
            break
        list_id, func, args, kwargs = item
        # if list_id.startswith(Prefix.PASSWORD_COLLISION.value):
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            result = 6, e
            result_queue.put((list_id, result))
        else:

            result_queue.put((list_id, result))


class ProcessResourceManager:
    def __init__(self, max_queue_size: int):
        self.manager = Manager()
        self.task_queue = self.manager.Queue(maxsize=max_queue_size)
        self.result_queue = self.manager.Queue()
        self.log_queue = self.manager.Queue()
        # self.counter = self.manager.Value('i', 0)
        self.lock = self.manager.Lock()
        self.list_counters = self.manager.dict()  # 存储列表总任务数
        self.list_progress = self.manager.dict()  # 存储列表任务进度
        self.list_events = self.manager.dict()  # 每个列表的完成事件
        self.list_status = self.manager.dict()  # 存储每个列表的状态

    def submit(self, list_id, func, *args, **kwargs):
        self.task_queue.put((list_id, func, args, kwargs), block=True)

    def set_list_total(self, list_id: str, total: int):
        """手动设置该列表的总任务数（需在提交任务前调用）"""
        with self.lock:
            self.list_counters[list_id] = total
            self.list_progress[list_id] = 1
            self.list_events[list_id] = self.manager.Event()  # 创建事件对象
            self.list_status[list_id] = {'completed': False, 'error': None}


class ProcessPool:
    def __init__(self, max_workers: int, resource_manager: ProcessResourceManager):
        self.resource = resource_manager

        self.workers = []

        # 启动结果处理器作为守护进程
        self.result_processor = Process(
            target=_monitor,
            args=(
                self.resource.result_queue, self.resource.lock, self.resource.list_counters,
                self.resource.list_progress, self.resource.list_events,
                self.resource.list_status, self.resource.log_queue),
            daemon=True  # 设置为守护进程
        )
        self.result_processor.start()

        for _ in range(max_workers):
            worker = Process(
                target=_worker_loop,
                args=(self.resource.task_queue, self.resource.result_queue),
                daemon=False
            )
            worker.start()
            self.workers.append(worker)

    def wait_all(self):
        while True:
            with self.resource.lock:
                if self.resource.result_queue.empty():
                    break
            time.sleep(0.1)

    def shutdown(self):
        self.wait_all()
        for _ in range(len(self.workers)):
            self.resource.task_queue.put(None)
        for worker in self.workers:
            worker.join()
        self.resource.result_queue.put(None)


def _monitor(result_queue, lock, list_counters, list_progress, list_events, list_status, log_queue):
    while True:
        try:
            item = result_queue.get(timeout=0.5)
            if item is None:
                print(f"关闭进度监视器")
                break
            list_id, result = item
            count_result(result, list_counters, list_events, list_id, list_status, lock, list_progress, log_queue)

        except queue.Empty:
            pass


def count_result(result, list_counters, list_events, list_id: str, list_status, lock, progress, log_queue):
    total = list_counters.get(list_id, 0)
    if list_id.startswith(Prefix.UNZIP.value):
        code, msg = result
        if code == 0:
            with lock:
                # if progress[list_id] == 0:
                #     progress[list_id] += 1
                progress[list_id] += 1
                current = progress[list_id]
                if current >= total:  # 完成所有任务
                    list_status[list_id] = {'completed': True, 'error': None}
                    list_events[list_id].set()  # 触发事件
            print(f"进度：任务 {list_id} 已完成 {current}/{total}  使用密码:{msg}")
            # log_queue.put((list_id, f"进度：任务 {list_id} 已完成 {current}/{total}  使用密码:{msg}"))

        else:
            list_status[list_id] = {'completed': False, 'error': msg}
            list_events[list_id].set()
            print(f"任务失败（列表：{list_id}， 已完成 {0}/{total}  错误：{str(msg)}）")
            # log_queue.put((list_id, f"任务失败（列表：{list_id}， 已完成 {0}/{total}  错误：{str(msg)}）"))
    elif list_id.startswith(Prefix.PASSWORD_COLLISION.value):
        print(f"list_id:{list_id} completed ,result:{result}")
        if result:
            list_status[list_id] = {'completed': True, 'error': False, 'password': result}
            print('任务完成')
        else:
            list_status[list_id] = {'completed': True, 'error': 'NO PASSWORD'}
            print('任务失败')
    #         list_events[list_id].set()  # 触发事件
