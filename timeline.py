import os


class Archive:
    def __init__(self, file):
        self.path = file
        self.father, self.name = os.path.split(file)  # 所在文件夹,文件名
        self.filename, self.extension = os.path.splitext(self.name)  # 文件名，文件扩展名
        self.file_list = []
        if os.path.isdir(file):
            tmp_list = []
            for root, dirs, files in os.walk(file):
                for item in files:
                    tmp_list.append(os.path.join(root, item))
            self.file_list = tmp_list


class Record:
    def __init__(self, input_file: Archive, ops, output_file: Archive = None, finish_time=None):
        self.input_file: Archive = input_file
        self.output_file: Archive = output_file
        self.ops = ops
        self.finish_time = finish_time


class Timeline:
    def __init__(self, records: list[Record]):
        self.records = records

    def get_all_archives(self):
        archives_list = []
        for record in self.records:
            archives_list.append(record.input_file)
        return archives_list

    def add_record(self, new_record: Record):
        self.records.append(new_record)
