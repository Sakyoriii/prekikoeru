import logging
import re
from logging import handlers

default_formatter: logging.Formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
gui = None


def extract_fraction(fraction_string):
    # 使用正则表达式匹配分数
    try:
        match = re.search(r'(\d+)/(\d+)', fraction_string)
        if match:
            numerator = int(match.group(1))  # 提取分子
            denominator = int(match.group(2))  # 提取分母
            return numerator, denominator
        else:
            return None, None
    except Exception:
        return None, None


class LogHandler(logging.Handler):
    def __init__(self, name):
        logging.Handler.__init__(self)
        self.level = logging.DEBUG
        self.name = name
        formatter = default_formatter
        self.setFormatter(formatter)

    def emit(self, record):
        # try:

        value, maximum = extract_fraction(record.msg)
        if value and maximum:
            gui.update_progress(value, maximum, record.msg)
        else:
            format_msg = self.format(record)
            msg = format_msg + '\n'
            evt = gui.write(msg)


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
            file_handler = handlers.RotatingFileHandler(file, 'a', 1240 * 1240 * 5, 3, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.__logger.addHandler(file_handler)

    def get_logger(self):
        return self.__logger

    def add_log_handler(self):
        log_handler = LogHandler(self.name)
        self.__logger.addHandler(log_handler)
        return self
