import pk_logger
from timeline import Archive

# logger = pk_logger.Pk_logger('unzip_logger', 'log.txt').add_log_handler().get_logger()


class Zip(Archive):

    def __init__(self, file, password_list: list = [], del_after_unzip: bool = False, jap: bool = False
                 , covered: bool = False,
                 volumes: list = None):
        super(Zip, self).__init__(file)
        self.pw_list = []
        self.compression_ratio_info = {}
        self.del_after_unzip = del_after_unzip
        self.jap = jap
        self.covered = covered
        self.set_password(password_list)
        self.volumes = volumes


    def set_password(self, password_list):
        self.pw_list = password_list
        self.pw_list.insert(0, self.filename)
        if self.RJ_code:
            self.pw_list.insert(0, self.RJ_code)

    def set_note(self, note):
        self.pw_list.insert(0, note)
        is_rj = self.RJ_code is not None
        super(Zip, self).set_note(note)
        if not is_rj and self.RJ_code:
            self.pw_list.insert(0, self.RJ_code)

    def extend(self, old: Archive):
        if self.RJ_code is None and old.RJ_code:
            self.RJ_code = old.RJ_code
            self.pw_list.insert(0, self.RJ_code)
        if old.note:
            self.set_note(old.note)
