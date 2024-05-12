import sys
import os


import yaml

from .config_file import ConfigFile
from .renamer import Renamer
from scaner import Scaner
from scraper import Locale, CachedScraper

path = 'C:\\Users\\75219\\Desktop\\新建文件夹\\dir\\RJ250978'
config_file_path = os.path.join('..\config.yaml')


def run_renamer(path):
    # self.__before_worker_thread_start()

    try:
        config = ConfigFile(config_file_path).load_config()  # 从配置文件中读取配置
    except yaml.YAMLError as err:
    # except JSONDecodeError as err:
        # self.__print_error(f'配置文件解析失败："{os.path.normpath(self.__config_file.file_path)}"')
        # self.__print_error(f'JSONDecodeError: {str(err)}')
        # self.__before_worker_thread_end()
        print(err)
        return
    except FileNotFoundError as err:
        # self.__print_error(f'配置文件加载失败："{os.path.normpath(self.__config_file.file_path)}"')
        # self.__print_error(f'FileNotFoundError: {err.strerror}')
        # self.__before_worker_thread_end()
        print(err)
        return

    # 检查配置是否合法
    strerror_list = ConfigFile.verify_config(config)
    if len(strerror_list) > 0:
        # self.__print_error(f'配置文件验证失败："{os.path.normpath(self.__config_file.file_path)}"')
        print(f'配置文件验证失败："{os.path.normpath(path)}"')
        for strerror in strerror_list:
            # self.__print_error(strerror)
            print(strerror)
        # self.__before_worker_thread_end()
        return

    # 配置 scaner
    scaner_max_depth = config['scaner_max_depth']
    scaner = Scaner(max_depth=scaner_max_depth)

    # 配置 scraper
    scraper_locale = config['scraper_locale']
    scraper_http_proxy = config['scraper_http_proxy']
    if scraper_http_proxy:
        proxies = {
            'http': scraper_http_proxy,
            'https': scraper_http_proxy
        }
    else:
        proxies = None
    scraper_connect_timeout = config['scraper_connect_timeout']
    scraper_read_timeout = config['scraper_read_timeout']
    scraper_sleep_interval = config['scraper_sleep_interval']
    cached_scraper = CachedScraper(
        locale=Locale[scraper_locale],
        connect_timeout=scraper_connect_timeout,
        read_timeout=scraper_read_timeout,
        sleep_interval=scraper_sleep_interval,
        proxies=proxies)
    tags_option = {
        'ordered_list': config['renamer_tags_ordered_list'],
        'max_number': 999999 if config['renamer_tags_max_number'] == 0 else config['renamer_tags_max_number'],
    }

    # 配置 dlrenamer
    renamer = Renamer(
        scaner=scaner,
        scraper=cached_scraper,
        template=config['renamer_template'],
        release_date_format=config['renamer_release_date_format'],
        delimiter=config['renamer_delimiter'],
        cv_list_left=config['cv_list_left'],
        cv_list_right=config['cv_list_right'],
        exclude_square_brackets_in_work_name_flag=config['renamer_exclude_square_brackets_in_work_name_flag'],
        renamer_illegal_character_to_full_width_flag=config['renamer_illegal_character_to_full_width_flag'],
        make_folder_icon=config['make_folder_icon'],
        remove_jpg_file=config['remove_jpg_file'],
        tags_option=tags_option)

    # 执行重命名
    # for path in path_list:
    for p in path:
        renamer.rename(p)

# run_renamer(path)