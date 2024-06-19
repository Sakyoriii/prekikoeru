import os
import queue

import tkinter as tk
from tkinter import ttk

import windnd

import config
import main
import file_ops
import pk_logger
import unzip

global flag


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

        self.labelframe = tk.LabelFrame(self, text='任务', padx=18)
        self.labelframe2 = tk.LabelFrame(self, text='log')
        self.radio1 = tk.Radiobutton(self.labelframe, text='解压', variable=self.val, value='unzip',
                                     command=lambda: self.clear())
        self.radio1.select()
        self.radio2 = tk.Radiobutton(self.labelframe, text='过滤', variable=self.val, value='filter',
                                     command=lambda: self.clear())
        self.radio3 = tk.Radiobutton(self.labelframe, text='重命名', variable=self.val, value='rename',
                                     command=lambda: self.clear())
        # self.radio4 = tk.Radiobutton(self.labelframe, text='结果', variable=self.val, value='result',
        #                              command=lambda: self.result())

        self.btn1 = tk.Button(self, text='清空', command=lambda: self.clear())
        self.btn2 = tk.Button(self, text='开冲', command=lambda: self.dash())
        self.btn3 = tk.Button(self, text='设置', command=lambda: os.system('start ' + 'config.yaml'))

        self.btn4 = tk.Button(self, text='输出', command=lambda: os.system('start ' + main.output_path))
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
        # self.radio4.pack(side='top')
        self.btn1.pack()
        self.btn2.pack()
        self.btn3.pack()
        self.btn4.pack()
        self.btn5.pack()

        self.pack(fill=tk.BOTH, expand=True)

    def write(self, info):
        # info信息即标准输出sys.stdout和sys.stderr接收到的输出信息
        self.text.insert('end', info)  # 在多行文本控件最后一行插入print信息
        self.text.update()  # 更新显示的文本，不加这句插入的信息无法显示
        self.text.see(tk.END)  # 始终显示最后一行，不加这句，当文本溢出控件最后一行时，不会自动显示最后一行

    def result(self):
        self.add2lisbox(main.result_queue)

    def clear(self):
        main.task_queue = queue.Queue()

        self.add2lisbox(queue.Queue())

    def add2lisbox(self, queue: queue.Queue):
        self.listbot1.delete(0, tk.END)
        qlist = list(queue.queue)
        for item in qlist:
            self.listbot1.insert(tk.END, item)
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
        config.init()

        self.btn2.configure(stat=tk.DISABLED)
        process = str(self.val.get())
        if process == 'unzip':
            unzip.unzip_main()
            self.val.set('filter')
        elif process == 'filter':
            file_ops.filter_main()
            self.val.set('rename')
        elif process == 'rename':
            file_ops.rename_main()
        else:
            self.btn2.configure(stat=tk.NORMAL)
            return

        # 当前队列完成，把下一个队列的任务加入到任务队列后清空任务队列
        if not main.next_queue.empty():
            main.task_queue = main.next_queue
            main.next_queue = queue.Queue()

        self.add2lisbox(main.task_queue)
        if main.auto_next and not process == 'rename':
            self.after(1000, func=self.dash)
        self.btn2.configure(stat=tk.NORMAL)


def on_drop(files):
    print('start')
    zlist = []
    process = str(pk_logger.gui.val.get())

    qlist = list(main.task_queue.queue)
    if process == 'unzip':
        for zip in qlist:
            zlist.append(zip.path)
    else:
        for zip in qlist:
            zlist.append(zip)

    if files:
        for item in files:
            file = item.decode('gbk')
            if file in zlist:
                continue
            if process == 'unzip':
                file_ops.find_zip(file, main.del_after_unzip)
            else:
                main.task_queue.put(file)
            pk_logger.gui.add2lisbox(main.task_queue)


def init_ui():
    window = tk.Tk()
    window.title("prekikoeru")
    window.geometry('1280x648')
    console = Console(window)
    console.pack(fill=tk.BOTH, expand=True)

    pk_logger.gui = console

    windnd.hook_dropfiles(window, func=on_drop)
    config.init()
    window.mainloop()
