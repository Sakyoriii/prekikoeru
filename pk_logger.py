import logging
from logging import handlers

default_formatter: logging.Formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
gui = None


class LogHandler(logging.Handler):
    def __init__(self, name):
        logging.Handler.__init__(self)
        self.level = logging.DEBUG
        self.name = name
        formatter = default_formatter
        self.setFormatter(formatter)

    def emit(self, record):
        # try:
        msg = self.format(record) + '\n'
        evt = gui.write(msg)
    # except (KeyboardInterrupt, SystemExit) as err:
    #     raise err
    # except Exception:
    #     self.handleError(record)


class Pk_logger(object):
    def __init__(self, name: str, file: str = None):
        self.name = name
        self.__logger = logging.getLogger(name=name)
        self.__logger.setLevel(logging.DEBUG)
        stderr_handler: logging.StreamHandler = logging.StreamHandler()
        formatter = default_formatter
        stderr_handler.setFormatter(formatter)
        self.__logger.addHandler(stderr_handler)

        if file:
            file_handler = handlers.RotatingFileHandler(file, 'a', 1240*1240*5, 3, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.__logger.addHandler(file_handler)

    def get_logger(self):
        return self.__logger

    def add_log_handler(self):
        log_handler = LogHandler(self.name)
        self.__logger.addHandler(log_handler)
        return self
