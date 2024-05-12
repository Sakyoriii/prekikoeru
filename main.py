# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import queue


import gui

passwords = []  # 密码数组
task_queue = queue.Queue()  # 任务队列
next_queue = queue.Queue()  # 下个队列
result_queue = queue.Queue()  # 未完成列表

output_path = ""
recycle_path = ""
logical_deletion = True  # 逻辑删除，实际上移到回收地址中
del_after_unzip = False
del_after_merged = True
del_after_merged_and_unzip = True
del_after_reunzip = True  # 是否删除套娃压缩包，是中间生成的压缩包不是源包哦
filte_dir = True
filter_kw = []
max_thread = 2
auto_next = False  # 是否自动继续下一步


if __name__ == '__main__':

    gui.init_ui()





