import os

import yaml

import pk_logger
from dlrenamer.config_file import ConfigFile

logger = pk_logger.Pk_logger('config_logger', 'log.txt').add_log_handler().get_logger()


class Config:
    def __init__(self):
        config = get_config('config.yaml')
        self.output_path = config['path']['output']
        self.recycle_path = config['path']['recycle']
        self.logical_deletion = config['logical_deletion']
        self.del_after_unzip = config['del_after_unzip']
        self.filter_kw = config['filter']['keyword']
        self.filter_dir = config['filter']['filte_dir']
        self.del_after_reunzip = config['del_after_reunzip']
        self.auto_next = config['auto_next']
        self.max_thread = config['max_thread']
        self.thread_threshold_mb = config['thread_threshold_mb']
        self.thread_compression_ratio = config['thread_compression_ratio']
        self.blacklist = config['blacklist']



    def load_config(self):
        print('load config')
        config = get_config('config.yaml')
        self.output_path = config['path']['output']
        self.recycle_path = config['path']['recycle']
        self.logical_deletion = config['logical_deletion']
        self.del_after_unzip = config['del_after_unzip']
        self.filter_kw = config['filter']['keyword']
        self.filter_dir = config['filter']['filte_dir']
        self.del_after_reunzip = config['del_after_reunzip']
        self.auto_next = config['auto_next']
        self.max_thread = config['max_thread']
        self.thread_threshold_mb = config['thread_threshold_mb']
        self.thread_compression_ratio = config['thread_compression_ratio']
        self.blacklist = config['blacklist']


def get_config(path):
    try:
        config = ConfigFile(path).load_config()  # 从配置文件中读取配置
        return config
    except yaml.YAMLError as err:
        logger.error(f'配置文件解析失败："{os.path.normpath(path)}"')
        logger.error(f'JSONDecodeError: {str(err)}')
        return
    except FileNotFoundError as err:
        logger.error(f'配置文件加载失败："{os.path.normpath(path)}"')
        logger.error(f'FileNotFoundError: {err.strerror}')
        return



