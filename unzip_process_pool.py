import multiprocessing
import queue
import time
from collections import defaultdict
from multiprocessing import Process, Manager


def _worker_loop(queue, result_queue):
    while True:
        item = queue.get()
        if item is None:
            break
        list_id, func, args, kwargs = item
        result_code, msg = func(*args, **kwargs)
        success = result_code == 0

        # with lock:
        #     counter.value -= 1
        # 将 list_id 和结果传递给 result_processor
        result_queue.put((list_id, success, msg))


class UnzipProcessPool:
    def __init__(self, max_workers: int, max_queue_size: int, progress_ui):
        self.manager = Manager()
        self.task_queue = self.manager.Queue(maxsize=max_queue_size)
        self.result_queue = self.manager.Queue()
        # self.counter = self.manager.Value('i', 0)
        self.lock = self.manager.Lock()
        self.list_counters = self.manager.dict()  # 存储列表总任务数
        self.list_events = self.manager.dict()  # 每个列表的完成事件
        self.list_status = self.manager.dict()  # 存储每个列表的状态
        self.workers = []
        self.progress_ui = progress_ui

        # 启动结果处理器作为守护进程
        self.result_processor = Process(
            target=_monitor,
            args=(self.result_queue, self.lock, self.list_counters, self.list_events, self.list_status),
            daemon=True  # 设置为守护进程
        )
        self.result_processor.start()

        for _ in range(max_workers):
            worker = Process(
                target=_worker_loop,
                args=(self.task_queue, self.result_queue),
                daemon=False
            )
            worker.start()
            self.workers.append(worker)

    # def submit(self, list_id: str, func: Callable, *args, **kwargs):
    #     # with self.lock:
    #     #     self.counter.value += 1
    #     self.task_queue.put((list_id, func, args, kwargs), block=True)

    def set_list_total(self, list_id: str, total: int):
        """手动设置该列表的总任务数（需在提交任务前调用）"""
        with self.lock:
            self.list_counters[list_id] = total
            self.list_events[list_id] = self.manager.Event()  # 创建事件对象
            self.list_status[list_id] = {'completed': False, 'error': None}

    def wait_all(self):
        while True:
            with self.lock:
                if self.result_queue.empty():
                    break
            time.sleep(0.1)

    def shutdown(self):
        self.wait_all()
        for _ in range(len(self.workers)):
            self.task_queue.put(None)
        for worker in self.workers:
            worker.join()
        self.result_queue.put(None)


def cpu_intensive_task(task_id: int):
    time.sleep(2)  # 模拟耗时任务
    return 1, 'finishhh'


def _monitor(result_queue, lock, list_counters, list_events, list_status):
    progress = defaultdict(int)
    while True:
        try:
            item = result_queue.get(timeout=0.5)
            if item is None:
                print(f"关闭进度监视器")
                break
            list_id, success, result = item
            total = list_counters.get(list_id, 0)
            if success:
                with lock:
                    if progress[list_id] == 0:
                        progress[list_id] += 1
                    progress[list_id] += 1
                    current = progress[list_id]
                    if current >= total:  # 完成所有任务
                        list_status[list_id] = {'completed': True, 'error': None}
                        list_events[list_id].set()  # 触发事件
                print(f"进度：任务 {list_id} 已完成 {current}/{total}  信息:{result.splitlines()[-4]}")
            else:
                list_status[list_id] = {'completed': False, 'error': result}
                list_events[list_id].set()
                print(f"任务失败（列表：{list_id}，错误：{str(result)}）")

            # 检查是否所有任务完成
            # with lock:
            #     if counter.value == 0 and result_queue.empty():
            #         print("所有任务已完成，退出")
            #         break

        except queue.Empty:
            pass


# def submit(task_queue, list_id: str, func: Callable, *args, **kwargs):
#     # with self.lock:
#     #     self.counter.value += 1
#     task_queue.put((list_id, func, args, kwargs), block=True)


def submit_process(task_queue, events, statuses, list_id: str, tasks: list):
    fun_sub = lambda t_queue, l_id, func, *args, **kwargs: t_queue.put((l_id, func, args, kwargs), block=True)
    for task in tasks:
        # submit(task_queue, list_id, cpu_intensive_task, task)
        fun_sub(task_queue, list_id, cpu_intensive_task, task)
        print(f"提交任务{task} 到 {list_id} ({time.time() :.2f}s)")

    # 阻塞等待该任务组完成
    event = events[list_id]
    event.wait()
    status = statuses[list_id]
    if status['completed']:
        print(f"进程{list_id}任务组完成，执行后续操作")
    else:
        print(f"进程{list_id}任务组失败: {status['error']}")


if __name__ == "__main__":
    multiprocessing.freeze_support()
    pool = UnzipProcessPool(max_workers=3, max_queue_size=2, progress_ui='s')
    task_lists = {
        "list1": [1, 2, 3],
        "list2": [4, 5]
    }
    processes = []
    start_time = time.time()
    # 设置每个列表的总任务数
    for list_id, tasks in task_lists.items():
        pool.set_list_total(list_id, len(tasks))
        # submit(list_id,tasks)
        p = Process(
            target=submit_process,
            args=(pool.task_queue, pool.list_events, pool.list_status, list_id, tasks),
        )
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    pool.shutdown()

    print(f"总耗时: {time.time() - start_time:.2f}s")
