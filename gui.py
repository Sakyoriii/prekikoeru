import os
import queue

import tkinter as tk
from tkinter import ttk, simpledialog

import windnd

import pk_logger

import task_runner

UI = None
output = ''


class Console(tk.Frame):

    def __init__(self, master, *args, **kwargs):
        tk.Frame.__init__(self, master, *args, **kwargs)

        self.val = tk.StringVar()
        self.val2 = tk.StringVar()
        self.val3 = tk.StringVar()
        self.val2.set('待机')
        self.val3.set(' ')

        self.label1 = tk.Label(self, text='待处理')

        self.meun1 = tk.StringVar()
        self.meun1.set('')
        self.listbot1 = tk.Listbox(self, listvariable=self.meun1)
        self.listbot1.bind("<Double-1>", self.note)

        self.labelframe = tk.LabelFrame(self, text='任务', padx=18)
        self.labelframe2 = tk.LabelFrame(self, text='log')
        self.radio1 = tk.Radiobutton(self.labelframe, text='解压', variable=self.val, value='unzip',
                                     command=lambda: self.clear())
        self.radio1.select()
        self.radio2 = tk.Radiobutton(self.labelframe, text='插入RJ', variable=self.val, value='insert_rj',
                                     command=lambda: self.clear())
        self.radio3 = tk.Radiobutton(self.labelframe, text='过滤', variable=self.val, value='filter',
                                     command=lambda: self.clear())
        self.radio4 = tk.Radiobutton(self.labelframe, text='重命名', variable=self.val, value='rename',
                                     command=lambda: self.clear())

        self.btn1 = tk.Button(self, text='清空', command=lambda: self.clear())
        self.btn2 = tk.Button(self, text='开冲', command=lambda: self.dash())
        self.btn3 = tk.Button(self, text='设置', command=lambda: os.system('start ' + 'config.yaml'))

        self.btn4 = tk.Button(self, text='输出', command=lambda: os.system('start ' + output))
        self.btn5 = tk.Button(self, text='密码', command=lambda: os.system('start ' + 'password.txt'))

        self.frame = tk.Frame(self)
        self.label2 = tk.Label(self.frame, textvariable=self.val2)
        self.label3 = tk.Label(self.frame, textvariable=self.val3)
        self.progressbar = ttk.Progressbar(self.frame, length=233, value=1)
        self.text = tk.Text(self.labelframe2, background="black", foreground="white", font=("Arial", 12))
        self.frame.pack(fill='x', expand=True, side='bottom')
        self.progressbar.pack(side='right', padx=20)
        self.label3.pack(side='left')
        self.label2.pack(side='left')
        self.labelframe2.pack(fill='x', side='bottom', padx=10)
        self.text.pack(fill='x', expand=True, side='bottom')
        self.label1.pack(side='top', anchor='w')
        self.listbot1.pack(fill='y', expand=True, ipadx=488, side='left')
        self.labelframe.pack(fill='y', expand=True, side='left')
        self.radio1.pack(side='top')
        self.radio2.pack(side='top')
        self.radio3.pack(side='top')
        self.radio4.pack(side='top')
        # self.radio4.pack(side='top')
        self.btn1.pack()
        self.btn2.pack()
        self.btn3.pack()
        self.btn4.pack()
        self.btn5.pack()

        self.pack(fill=tk.BOTH, expand=True)

    def note(self, event):
        index = self.listbot1.curselection()
        if index:
            i = index[0]
            new_text = simpledialog.askstring("备注", "备注RJ/密码")
            if new_text:
                # # 获取当前项的文本
                # current_text = self.listbot1.get(index)
                # # 更新项的文本
                # self.listbot1.delete(index)
                # self.listbot1.insert(index, current_text + new_text)
                task_runner.timelines[i].get_current_record().output_file.set_note(new_text)

    def write(self, info):
        # info信息即标准输出sys.stdout和sys.stderr接收到的输出信息
        self.text.insert('end', info)  # 在多行文本控件最后一行插入print信息
        self.text.update()  # 更新显示的文本，不加这句插入的信息无法显示
        self.text.see(tk.END)  # 始终显示最后一行，不加这句，当文本溢出控件最后一行时，不会自动显示最后一行

    def clear(self):
        task_runner.clear()
        task_runner.already_add = []
        self.add2lisbox(queue.Queue())

    def add2lisbox(self, queue: queue.Queue):
        self.listbot1.delete(0, tk.END)
        qlist = list(queue.queue)
        for item in qlist:
            record = item.get_current_record()
            self.listbot1.insert(tk.END, (record.input_file.path, record.ops))
        self.update()

    def add2lis(self, list):
        self.listbot1.delete(0, tk.END)
        for item in list:
            record = item.get_current_record()
            self.listbot1.insert(tk.END, f"[{record.input_file.name}] == {record.ops} == > [{record.output_file.name}]")
        self.update()

    def update_progress(self, value, maximum, title):
        text = ' {}'.format(title)
        text2 = '{}/{} :'.format(value, maximum)
        self.val3.set(text2)
        self.val2.set(text)
        now = int(value * 100 / maximum)
        self.progressbar['value'] = now
        self.update()

    def dash(self):

        self.btn2.configure(stat=tk.DISABLED)
        process = str(self.val.get())
        # task_list = list(main.task_queue.queue)
        static_task_list = ['unzip', 'insert_rj', 'filter', 'rename']
        index = static_task_list.index(process)
        exec(f'task_runner.{process}_loop()')

        # if process == 'unzip':
        #     task_runner.unzip_loop(self)
        #     self.val.set('insert_rj')
        # elif process == 'insert_rj':
        #     # for timeline in task_list:
        #     task_runner.insert_rj_loop(self)
        #     # self.add2lisbox(main.task_queue)
        #     self.val.set('filter')
        # elif process == 'filter':
        #     # for timeline in task_list:
        #     #     task_runner.filter_main(timeline)
        #     # main.next_queue.put(timeline)
        #     # self.add2lisbox(main.next_queue)
        #     task_runner.filter_loop(self)
        #     self.val.set('rename')
        # elif process == 'rename':
        #     # task_runner.rename_main()
        #     task_runner.remame_loop(self)
        #     self.btn2.configure(stat=tk.NORMAL)
        #     return

        self.btn2.configure(stat=tk.NORMAL)
        if index < len(static_task_list) - 1:
            self.val.set(static_task_list[index + 1])

            if task_runner.conf.auto_next:
                self.dash()

        # 当前队列完成，把下一个队列的任务加入到任务队列后清空任务队列
        # if not main.next_queue.empty():
        #     main.task_queue = main.next_queue
        #     main.next_queue = queue.Queue()

        # self.add2lisbox(main.task_queue)
        # if True and not process == 'rename':
        #     task_runner.remame_loop(self)
        #     self.clear()
        # self.btn2.configure(stat=tk.NORMAL)


def on_drop(files):
    print('start')
    global UI
    process = str(UI.val.get())

    task_runner.reload()
    if files:
        for i in range(len(files)):
            files[i] = files[i].decode('gbk')

        i = ['unzip', 'insert_rj', 'filter', 'rename'].index(process)
        task_runner.create_timeline(files, i)


def init_ui():
    window = tk.Tk()
    window.title("prekikoeru_v0.1")
    window.geometry('1280x648')
    console = Console(window)
    console.pack(fill=tk.BOTH, expand=True)
    # global output
    # output = task_runner.conf.output_path
    pk_logger.gui = console
    global UI
    UI = console
    task_runner.progress_ui = console
    # task_runner.unzipper.progress_ui = console
    windnd.hook_dropfiles(window, func=on_drop)
    window.mainloop()
