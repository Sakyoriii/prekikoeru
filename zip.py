import re

import pk_logger
from timeline import Archive

logger = pk_logger.Pk_logger('unzip_logger', 'log.txt').add_log_handler().get_logger()


class Zip(Archive):

    def __init__(self, file, password_list: list = [], del_after_unzip: bool = False, jap: bool = False
                 , covered: bool = False, note: str = None,
                 volumes: list = None):
        super(Zip, self).__init__(file)
        self.pw_list = []
        self.del_after_unzip = del_after_unzip
        self.jap = jap
        self.covered = covered
        self.RJ_code = None
        # 匹配文件名或备注中Rj号，插入密码表
        self.getRJ(self.name)
        if note:
            self.note = note
            self.getRJ(note)
        self.set_password(password_list)
        self.volumes = volumes

    def getRJ(self, string: str):
        RJ = re.compile(r'[RBV]J(\d{6}|\d{8})(?!\d+)').search(string.upper())
        if RJ:
            self.RJ_code = RJ.group()

    def set_password(self, password_list):
        self.pw_list = password_list
        self.pw_list.insert(0, self.filename)
        if self.RJ_code:
            self.pw_list.insert(0, self.RJ_code)

    def set_note(self, note):
        self.note = note
        self.getRJ(note)
        if self.RJ_code:
            self.pw_list.insert(0, self.RJ_code)

