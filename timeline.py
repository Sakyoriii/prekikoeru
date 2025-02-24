import os
import re
from datetime import datetime


class Archive:
    def __init__(self, file, note: str = None):
        self.path = file
        self.father, self.name = os.path.split(file)  # 所在文件夹,文件名
        self.filename, self.extension = os.path.splitext(self.name)  # 文件名，文件扩展名
        self.file_list = []  # 内容列表
        if os.path.isdir(file):
            tmp_list = []
            for root, dirs, files in os.walk(file):
                for item in files:
                    tmp_list.append(os.path.join(root, item))
            self.file_list = tmp_list
        self.RJ_code = None
        # 匹配文件名或备注中Rj号，插入密码表
        self.getRJ(self.name)
        self.note = None

    def __str__(self):
        return self.path

    def getRJ(self, string: str):
        RJ = re.compile(r'[RBV]J(\d{6}|\d{8})(?!\d+)').search(string.upper())
        if RJ:
            self.RJ_code = RJ.group()

    def set_note(self, note):
        self.note = note
        self.getRJ(note)
        print(self.name + " set note : " + note)


def extend(new: Archive, old: Archive):
    if old.RJ_code:
        new.RJ_code = old.RJ_code
    if old.note:
        new.set_note(old.note)


class Record:
    def __init__(self, input_file: Archive, ops, output_file: Archive = None, finish_time=datetime.now()):
        self.input_file: Archive = input_file
        self.output_file: Archive = output_file
        self.ops = ops
        self.finish_time = finish_time


class Timeline:
    def __init__(self, input_file: Archive, ops, output_file=None, task_list: list = None):
        self.records = [Record(input_file, ops, output_file)]

        self.task_list = task_list  # 任务列表
        self.task_process = 0  # 任务进度

    def __str__(self):
        str_list = ''
        for record in self.records:
            str_list += f' \n\n FINISH TIME :        {record.finish_time} \n INPUT FILE :        {record.input_file}' \
                        f'  \n OPERATE :        {record.ops} \n OUTPUT FILE :    {record.output_file} \n'
        return str_list

    def get_all_input_archives(self):
        archives_list = []
        for record in self.records:
            archives_list.append(record.input_file)
        return archives_list

    def get_all_output_archives(self):
        archives_list = []
        for record in self.records:
            if record.output_file:
                archives_list.append(record.output_file)
        return archives_list

    def get_current_record(self):
        return self.records[-1]

    def get_current_path(self):
        return self.records[-1].output_file.path if self.records[-1].output_file else self.records[-1].input_file.path

    def add_record(self, new_record: Record):
        self.records.append(new_record)

    # def add_record(self, input_file: Archive, ops, already_add: list = None):
    #     if already_add:
    #         already_add.append(input_file.path)
    #     # if next_task:
    #     #     self.task_process = next_task
    #     record = Record(input_file, ops)
    #     self.records.append(record)

    def set_process(self, process: int):
        self.task_process = process
        self.records[-1].ops = self.task_list[process]

    def set_process(self, ops: str):
        try:
            process = self.task_list.index(ops)
        except ValueError:
            return -1
        self.set_process(process)
        return process

    def add_output_path(self, path):
        self.records[-1].output_file = Archive(path)
