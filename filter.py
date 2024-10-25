import os
import re

import file_ops
import task_runner


class Filter():
    def __init__(self, keyword_list: list, filter_dir: bool, logger):
        self.keyword_list = keyword_list
        self.filter_dir = filter_dir
        self.logger = logger

    def pre_filter(self, file_list: list):
        result_list = []
        for file in file_list:
            for key in self.keyword_list:
                match = re.search(key, file.upper())
                if match:
                    self.logger.info('跳过文件夹: [ {} ] 命中关键词： [ {} ]'.format(file, key))
                    break
            else:
                result_list.append(file)
        return result_list

    def post_filter(self, path):
        if not os.path.exists(path):
            path = file_ops.get_similar_path(path)
        for root, dirs, files in os.walk(path):
            if dirs and self.filter_dir:
                for dir in dirs:
                    for key in self.keyword_list:
                        dir_path = os.path.join(root, dir)
                        match = re.search(key, dir_path.upper())
                        if match:
                            task_runner.delete_file(dir_path)
                            self.logger.info('过滤文件夹: [ {} ] 命中关键词： [ {} ]'.format(dir_path, key))
            if files:
                for file in files:
                    for key in self.keyword_list:
                        file_path = os.path.join(root, file)
                        match = re.search(key, file_path.upper())
                        if match:
                            task_runner.delete_file(file_path)
                            self.logger.info('过滤文件: [ {} ] 命中关键词： [ {} ]'.format(file_path, key))


