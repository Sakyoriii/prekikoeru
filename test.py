import logging
import os
import sys
import threading
import tkinter as tk

import file_ops
import main
import pk_logger

import time

# #
# class logHandler(logging.Handler):
#     def __init__(self, name, window):
#         logging.Handler.__init__(self)
#         self.level = logging.DEBUG
#         self.name = name
#         formatter: logging.Formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#         self.setFormatter(formatter)
#         self.window = window
#
#     def emit(self, record):
#         try:
#             msg = self.format(record) + '\n'
#             evt = self.window.write(msg)
#         except (KeyboardInterrupt, SystemExit) as err:
#             raise err
#         except Exception:
#             self.handleError(record)
#
#
# def log():
#     count = 0
#     while count < 5:
#         logger.info('test_logger!!!!')
#         count = count + 1
#         time.sleep(3)
#
#
# import tkinter as tk
#
#
# class Console(tk.Frame):
#
#     def __init__(self, master, *args, **kwargs):
#
#         tk.Frame.__init__(self, master, *args, **kwargs)
#
#         self.val = tk.StringVar()
#         self.label1 = tk.Label(self,text='待处理')
#
#
#
#         self.meun1 = tk.StringVar()
#         self.meun1.set('')
#         self.listbot1 = tk.Listbox(self, listvariable=self.meun1)
#
#         self.labelframe = tk.LabelFrame(self,text='任务',padx = 18)
#         self.radio1 = tk.Radiobutton(self.labelframe,text='解压',variable = self.val,value = 'unzip')
#         self.radio1.select()
#         self.radio2 = tk.Radiobutton(self.labelframe,text='过滤',variable = self.val,value = 'filter')
#         self.radio3 = tk.Radiobutton(self.labelframe,text='重命名',variable = self.val,value = 'rename')
#
#
#         self.btn1 = tk.Button(self, text='移除', command=lambda: self.listbot1.delete(self.listbot1.curselection())
#                               )
#         self.btn2 = tk.Button(self, text='开冲', command=lambda: self.listbot1.delete(self.listbot1.curselection())
#                               )
#         self.btn3 = tk.Button(self, text='设置', command=lambda: self.listbot1.delete(os.system('start '+ 'config.yaml'))
#                               )
#         self.btn4 = tk.Button(self, text='查看', command=lambda: self.listbot1.delete(os.system('start '+ main.output_path
#                                                                                               ))
#                               )
#
#         self.text = tk.Text(self, background="black", foreground="white", font=("Arial", 12))
#         self.text.pack(fill='x', expand=True, side='bottom')
#         self.label1.pack(side = 'top',anchor='w')
#         self.listbot1.pack(fill='y',expand = True,ipadx = 488, side='left')
#         self.labelframe.pack(fill = 'y',expand = True,side ='left')
#         self.radio1.pack(side='top')
#         self.radio2.pack(side='top')
#         self.radio3.pack(side='top')
#         self.btn1.pack()
#         self.btn2.pack()
#         self.btn3.pack()
#         self.btn4.pack()
#
#         self.pack(fill=tk.BOTH, expand=True)
#
#         # start the console
#         # self.process = subprocess.Popen("python", stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
#         # self.after(1000, self.refresh)
#
#     def write(self, info):
#         # info信息即标准输出sys.stdout和sys.stderr接收到的输出信息
#         self.text.insert('end', info)  # 在多行文本控件最后一行插入print信息
#         self.text.update()  # 更新显示的文本，不加这句插入的信息无法显示
#         self.text.see(tk.END)  # 始终显示最后一行，不加这句，当文本溢出控件最后一行时，不会自动显示最后一行
#
#     def refresh(self):
#         # get the output from the console
#         output = self.process.stdout.readline().decode("utf-8")
#         if output:
#             print(output)
#             self.text.insert(tk.END, output)
#             self.update()
#             self.text.see(tk.END)
#             # check if the console is still running
#         if self.process.poll() is None:
#             self.after(1000, self.refresh)
#
#
# root = tk.Tk()
# root.geometry("1280x600")
# console = Console(root)
# console.pack(fill=tk.BOTH, expand=True)
#
# logger = pk_logger.Pk_logger('test_Logger', 'log.txt').get_logger()
# log_handler = logHandler('test_log', console)
# logger.addHandler(log_handler)
#
# thread = threading.Thread(target=log)
# thread.start()
# print('run')
#
# root.mainloop()
#
#
# # print(file_ops.find_RJ(r'C:\Users\75219\Desktop\新建文件夹\dir\output'))
# main.compress_queue

# file_ops.move_last2first(r'C:\Users\75219\Desktop\新建文件夹\dir\output\RJ01176508')
file_ops.rm_taowadir(r'C:\Users\75219\Desktop\新建文件夹\dir\output\RJ01176508\2333')