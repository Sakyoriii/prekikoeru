import os

import yaml

import pk_logger
from dlrenamer.config_file import ConfigFile
import main

logger = pk_logger.Pk_logger('config_logger', 'log.txt').add_log_handler().get_logger()


def get_config(path):
    # with open(path, "r", encoding='utf-8') as conf:
    #     yconf = yaml.load(conf.read(), Loader=yaml.FullLoader)
    #     return yconf
    try:
        config = ConfigFile(path).load_config()  # 从配置文件中读取配置
        return config
    except yaml.YAMLError as err:
        logger.error(f'配置文件解析失败："{os.path.normpath(path)}"')
        logger.error(f'JSONDecodeError: {str(err)}')
        return
    except FileNotFoundError as err:
        # self.__print_error(f'配置文件加载失败："{os.path.normpath(self.__config_file.file_path)}"')
        # self.__print_error(f'FileNotFoundError: {err.strerror}')
        logger.error(f'配置文件加载失败："{os.path.normpath(path)}"')
        logger.error(f'FileNotFoundError: {err.strerror}')
        return


def read_password():
    tmp = []
    with open("password.txt", "r", encoding='utf-8') as pw:
        for line in pw.readlines():
            line = line.strip('\n')  # 去掉列表中每一个元素的换行符
            tmp.append(line)
    main.passwords = tmp


def load_config():
    print('load config')
    # with open("config.yaml", "r", encoding='utf-8') as conf:
    #     yconf = yaml.load(conf.read(), Loader=yaml.FullLoader)
    #
    config = get_config('config.yaml')
    main.output_path = config['path']['output']
    main.recycle_path = config['path']['recycle']
    main.logical_deletion = config['logical_deletion']
    main.del_after_unzip = config['del_after_unzip']
    main.filter_kw = config['filter']['keyword']
    # main.del_after_merged = config['del_after_merged']
    # main.del_after_merged_and_unzip = config['del_after_merged_and_unzip']
    main.del_after_reunzip = config['del_after_reunzip']
    main.auto_next = config['auto_next']
    main.max_thread = config['max_thread']


def init():
    load_config()
    read_password()
