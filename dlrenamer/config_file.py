import os
import re
from typing import TypedDict, Final, Optional

import yaml

from scraper import Locale


class Config(TypedDict):
    scaner_max_depth: int
    scraper_locale: str
    scraper_connect_timeout: int
    scraper_read_timeout: int
    scraper_sleep_interval: int
    scraper_http_proxy: Optional[str]
    renamer_template: str
    renamer_release_date_format: str
    renamer_exclude_square_brackets_in_work_name_flag: bool


class ConfigFile(object):
    DEFAULT_CONFIG: Final[Config] = {
        'path': {
            'output:': "dir/output",
            'recycle': "dir/recycle"
        },
        'logical_deletion': True,
        'del_after_unzip': False,
        'del_after_merged': True,
        'del_after_merged_and_unzip': True,
        'del_after_reunzip': True,
        'filte_dir': True,
        'auto_next': False,
        'max_thread': 2,
        'filter': {
            'keyword': [".*SE.*WAV"]
        },
        # dlsite-dlrenamer conf
        'scaner_max_depth': 2,
        'scraper_locale': 'zh_cn',
        'scraper_connect_timeout': 10,
        'scraper_read_timeout': 10,
        'scraper_sleep_interval': 3,
        'scraper_http_proxy': None,
        'renamer_template': '[rjcode][maker_name] work_name cv_list_str',
        # https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
        'renamer_release_date_format': '%y%m%d',
        'renamer_exclude_square_brackets_in_work_name_flag': False,
        'renamer_illegal_character_to_full_width_flag': False,
        'make_folder_icon': True,
        'remove_jpg_file': True,
        'renamer_delimiter': " ",  # 分隔符
        'cv_list_left': "(CV ",
        'cv_list_right': ")",
        'renamer_tags_max_number': 5,  # 标签个数上限
        'renamer_tags_ordered_list': ["标签1", ["标签2", "替换2"], "标签3"],  # 标签顺序列表，每一项可为字符串或[原标签,替换名]
    }

    def __init__(self, file_path: str):
        self.__file_path = file_path
        if not os.path.isfile(file_path):
            self.save_config(ConfigFile.DEFAULT_CONFIG)

    def load_config(self):
        """
        从配置文件中读取配置
        """
        with open(self.__file_path, "r", encoding='utf-8') as conf:
            yconf = yaml.load(conf.read(), Loader=yaml.FullLoader)

            # with open(self.__file_path, encoding='UTF-8') as file:
            #     config_dict: Config = json.load(file)
            config_dict: Config = yconf
            return config_dict

    def save_config(self, config_dict: Config):
        """
        保存配置到文件
        """
        with open(self.__file_path, 'w', encoding='UTF-8') as file:
            # json.dump(config_dict, file, indent=2, ensure_ascii=False)
            yaml.dump(data=config_dict, stream=file)

    @property
    def file_path(self):
        return self.__file_path

    @staticmethod
    def verify_config(config_dict: Config):
        """
        验证配置是否合理
        """
        scaner_max_depth = config_dict.get('scaner_max_depth', None)
        scraper_locale = config_dict.get('scraper_locale', None)
        scraper_connect_timeout = config_dict.get('scraper_connect_timeout', None)
        scraper_read_timeout = config_dict.get('scraper_read_timeout', None)
        scraper_http_proxy = config_dict.get('scraper_http_proxy', None)
        scraper_sleep_interval = config_dict.get('scraper_sleep_interval', None)
        renamer_template = config_dict.get('renamer_template', None)
        renamer_release_date_format = config_dict.get('renamer_release_date_format', None)
        renamer_exclude_square_brackets_in_work_name_flag = \
            config_dict.get('renamer_exclude_square_brackets_in_work_name_flag', None)
        renamer_illegal_character_to_full_width_flag = \
            config_dict.get('renamer_illegal_character_to_full_width_flag', None)
        make_folder_icon = \
            config_dict.get('make_folder_icon', None)
        remove_jpg_file = \
            config_dict.get('remove_jpg_file', None)
        renamer_tags_ordered_list = config_dict.get('renamer_tags_ordered_list', None)
        renamer_tags_max_number = config_dict.get('renamer_tags_max_number', None)
        renamer_delimiter = config_dict.get('renamer_delimiter', None)
        cv_list_left = config_dict.get('cv_list_left', None)
        cv_list_right = config_dict.get('cv_list_right', None)

        strerror_list = []

        # 检查 scaner_max_depth
        if not isinstance(scaner_max_depth, int) or scaner_max_depth < 0:
            strerror_list.append('scaner_max_depth 应是一个大于等于 0 的整数')

        # 检查 scraper_locale
        locale_name_list: list[str] = []
        for locale in Locale:
            locale_name_list.append(locale.name)
        if scraper_locale not in locale_name_list:
            strerror_list.append(f'scraper_locale 应是 {locale_name_list} 中的一个')

        # 检查 scraper_connect_timeout
        if not isinstance(scraper_connect_timeout, int) or scraper_connect_timeout <= 0:
            strerror_list.append('scraper_connect_timeout 应是一个大于 0 的整数')

        # 检查 scraper_read_timeout
        if not isinstance(scraper_read_timeout, int) or scraper_read_timeout <= 0:
            strerror_list.append('scraper_read_timeout 应是一个大于 0 的整数')

        # 检查 scraper_sleep_interval
        if not isinstance(scraper_sleep_interval, int) or scraper_sleep_interval < 0:
            strerror_list.append('scraper_sleep_interval 应是一个大于等于 0 的整数')

        # 检查 scraper_http_proxy
        http_proxy_pattern = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:(\d+)")
        str_error_http_proxy = f'scraper_http_proxy 应是形如 "127.0.0.1:7890" 的 http 代理；或设为 null，这将使用系统代理'
        if isinstance(scraper_http_proxy, str):
            if not http_proxy_pattern.fullmatch(scraper_http_proxy):
                # 是字符串但不匹配正则规则
                strerror_list.append(str_error_http_proxy)
        elif scraper_http_proxy is not None:
            # 既不是字符串也不是 None
            strerror_list.append(str_error_http_proxy)

        # 检查 renamer_template
        if not isinstance(renamer_template, str) or 'rjcode' not in renamer_template:
            strerror_list.append('renamer_template 应是一个包含 "rjcode" 的字符串')

        # 检查 renamer_release_date_format
        if not isinstance(renamer_release_date_format, str):
            strerror_list.append('renamer_release_date_format 应是一个字符串')

        # 检查 renamer_exclude_square_brackets_in_work_name_flag
        if not isinstance(renamer_exclude_square_brackets_in_work_name_flag, bool):
            strerror_list.append('renamer_exclude_square_brackets_in_work_name_flag 应是一个布尔值')

        # 检查 renamer_illegal_character_to_full_width_flag
        if not isinstance(renamer_illegal_character_to_full_width_flag, bool):
            strerror_list.append('renamer_illegal_character_to_full_width_flag 应是一个布尔值')

        # 检查 make_folder_icon
        if not isinstance(make_folder_icon, bool):
            strerror_list.append('make_folder_icon 应是一个布尔值')

        # 检查 remove_jpg_file
        if not isinstance(remove_jpg_file, bool):
            strerror_list.append('remove_jpg_file 应是一个布尔值')

        # 检查 renamer_tags_ordered_list
        if not isinstance(renamer_tags_ordered_list, list):
            strerror_list.append('renamer_tags_ordered_list 应是一个列表，其中每个元素是"标签名"或["标签名","替换名"]')
        else:
            for i in renamer_tags_ordered_list:
                if isinstance(i, list):
                    if not len(i) == 2 or not isinstance(i[0], str) or not isinstance(i[1], str):
                        strerror_list.append(f'renamer_tags_ordered_list 中每个元素应是"标签名"或["标签名","替换名"]，不能为【{i}】')
                elif not isinstance(i, str):
                    strerror_list.append(f'renamer_tags_ordered_list 中每个元素应是"标签名"或["标签名","替换名"]，不能为【{i}】')

        # 检查 renamer_tags_max_number
        if not isinstance(renamer_tags_max_number, int) or renamer_tags_max_number < 0:
            strerror_list.append('renamer_tags_max_number 应是大于等于 0 的整数。0为无限制')

        # 检查 renamer_delimiter
        if not isinstance(renamer_delimiter, str):
            strerror_list.append('renamer_delimiter 应是一个字符串')
        else:
            for i in renamer_delimiter:
                if i in r'\/:*?"<>|':
                    strerror_list.append(f'renamer_delimiter 不能含有系统保留字【{i}】')

        # 检查 cv_list_left
        if not isinstance(cv_list_left, str):
            strerror_list.append('cv_list_left 应是一个字符串')
        else:
            for i in cv_list_left:
                if i in r'\/:*?"<>|':
                    strerror_list.append(f'cv_list_left 不能含有系统保留字【{i}】')

        # 检查 cv_list_right
        if not isinstance(cv_list_right, str):
            strerror_list.append('cv_list_right 应是一个字符串')
        else:
            for i in cv_list_right:
                if i in r'\/:*?"<>|':
                    strerror_list.append(f'cv_list_right 不能含有系统保留字【{i}】')

        return strerror_list
