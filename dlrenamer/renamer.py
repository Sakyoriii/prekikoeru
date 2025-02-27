import logging
import os
import re
from pathlib import Path
from datetime import datetime

import requests
from requests.exceptions import RequestException, ConnectionError, HTTPError, Timeout

import pk_logger
from scaner import Scaner
from scraper import WorkMetadata, Scraper

import stat

import win32api

# Windows 系统的保留字符
# https://docs.microsoft.com/zh-cn/windows/win32/fileio/naming-a-file
# <（小于）
# >（大于）
# ： (冒号)
# "（双引号）
# /（正斜杠）
# \ (反反)
# | (竖线或竖线)
# ? （问号）
# * (星号)
WINDOWS_RESERVED_CHARACTER_PATTERN = re.compile(r'[\\/*?:"<>|]')
WINDOWS_RESERVED_CHARACTER_PATTERN_str = r'\/:*?"<>|'  # 半角字符，原
WINDOWS_RESERVED_CHARACTER_PATTERN_replace_str = '＼／：＊？＂＜＞｜'  # 全角字符，替


def _get_logger():
    # create logger
    # logger = logging.getLogger('Renamer')
    # logger.setLevel(logging.DEBUG)
    #
    # # create console handler and set level to debug
    # ch = logging.StreamHandler()
    # ch.setLevel(logging.DEBUG)
    # # create formatter
    # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # # add formatter to ch
    # ch.setFormatter(formatter)
    #
    # # add ch to logger
    # logger.addHandler(ch)
    logger = pk_logger.Pk_logger('dlrenamer', 'log.txt').add_log_handler().get_logger()

    return logger


class Renamer(object):
    logger = _get_logger()

    def __init__(
            self,
            scaner: Scaner,
            scraper: Scraper,
            template: str = '[maker_name][rjcode] work_name cv_list_str',  # 模板
            # https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
            release_date_format: str = '%y%m%d',  # 日期格式
            delimiter: str = ' ',  # 列表转字符串的分隔符
            cv_list_left: str = ' ',  # CV列表的左侧分隔符
            cv_list_right: str = ' ',  # CV列表的右侧分隔符
            exclude_square_brackets_in_work_name_flag: bool = False,  # 设为 True 时，移除 work_name 中【】及其间的内容
            renamer_illegal_character_to_full_width_flag: bool = False,  # 设为 True 时，新文件名将非法字符转为全角；为 False 时直接移除.
            make_folder_icon: bool = True,  # 设为 True 时，将会下载作品封面并将其设为文件夹封面
            remove_jpg_file: bool = True,  # 设为 True 时，将会保留下载的作品封面
            tags_option: dict = None,  # 标签相关设置
            rjcode_language_order=None,  # rj号 语言版本优先顺序
            title_language_order=None):  # 标题 语言版本优先顺序

        if 'rjcode' not in template:
            raise ValueError  # 重命名不能丢失 rjcode
        self.__scaner = scaner
        self.__scraper = scraper
        self.__template = template
        self.__release_date_format = release_date_format
        self.__delimiter = delimiter
        self.__cv_list_left = cv_list_left
        self.__cv_list_right = cv_list_right
        self.__exclude_square_brackets_in_work_name_flag = exclude_square_brackets_in_work_name_flag
        self.__renamer_illegal_character_to_full_width_flag = renamer_illegal_character_to_full_width_flag
        self.__make_folder_icon = make_folder_icon
        self.__remove_jpg_file = remove_jpg_file
        self.__tags_option = tags_option
        self.__rjcode_language_order = rjcode_language_order
        self.__title_language_order = title_language_order

    def __compile_new_name(self, metadata: WorkMetadata):
        """
        根据作品的元数据编写出新的文件名
        """
        # work_name = re.sub(r'【.*?】', '', metadata['work_name']).strip() \
        work_name = Renamer.remove_specific_brackets(metadata['work_name']) \
            if self.__exclude_square_brackets_in_work_name_flag \
            else metadata['work_name']

        template = self.__template
        new_name = template.replace('rjcode', metadata['rjcode'])
        new_name = new_name.replace('work_name', work_name)
        new_name = new_name.replace('maker_id', metadata['maker_id'])
        new_name = new_name.replace('maker_name', metadata['maker_name'])
        if 'release_date' in template:
            release_date_obj = datetime.strptime(metadata['release_date'], '%Y-%m-%d').date()
            new_name = new_name.replace('release_date', release_date_obj.strftime(self.__release_date_format))

        cv_list = metadata['cvs']  # cv列表
        cv_list_str = self.__cv_list_left + self.__delimiter.join(cv_list) + self.__cv_list_right if len(
            cv_list) > 0 else ''
        new_name = new_name.replace('cv_list_str', cv_list_str)

        if "tags_list_str" in self.__template:  # 标签列表
            tags_list = []
            tags_list_flag = []
            for i in self.__tags_option['ordered_list']:  # ordered_list中存在的标签
                if isinstance(i, str) and i in metadata['tags']:
                    tags_list.append(i)
                    tags_list_flag.append(i)
                elif isinstance(i, list) and i[0] in metadata['tags']:
                    tags_list.append(i[1])  # 替换新标签
                    tags_list_flag.append(i[0])
            for i in metadata['tags']:  # 剩余的标签
                if not i in tags_list_flag:
                    tags_list.append(i)
            tags_list = tags_list[: self.__tags_option['max_number']]  # 数量限制
            tags_list_str = self.__delimiter.join(tags_list)  # 转字符串，加分隔符
            new_name = new_name.replace('tags_list_str', tags_list_str)

        # 文件名中不能包含 Windows 系统的保留字符
        if self.__renamer_illegal_character_to_full_width_flag:  # 半角转全角
            new_name = new_name.translate(new_name.maketrans(
                WINDOWS_RESERVED_CHARACTER_PATTERN_str, WINDOWS_RESERVED_CHARACTER_PATTERN_replace_str))
        else:  # 直接移除
            new_name = WINDOWS_RESERVED_CHARACTER_PATTERN.sub('', new_name)

        return new_name.strip()

    @staticmethod
    def remove_specific_brackets(text):
        """
        删除包含语言标识、促销标识和设备标识的【】或[]内容。
        Args:
        text (str): 输入的字符串。
        Returns:
        str: 删除指定内容后的字符串。
        """

        # 定义需要删除的语言标识、促销标识和设备标识的正则表达式
        language_tags = r"繁体中文版|简体中文版|簡体中文版|简中&日文|日文版|中文版|中日英|中日|中文音声|简中字幕版|繁體中文版|中英日"
        promotion_tags = r".?特価.?|.?限定.?|.?特典.?|.?記念.?|.?割引.?|.?円.?|.?附赠.?|.?附加.?"
        device_tags = r"KU100ハイレゾ|KU100|ハイレゾ|96kHz/24bitハイレゾ|立体音響|バイノーラル|フォーリーサウンド|KU100バイノーラル|KU100高音質|KU100麦克风收录作品|KU100拟真音效|KU100高音质|KU100高解析度"

        # 合并所有需要删除的标识
        combined_tags = f"{language_tags}|{promotion_tags}|{device_tags}"

        # 删除包含指定标识的【】或[]内容
        pattern = rf"(\[({combined_tags})\])|(\【({combined_tags})\】)"
        text = re.sub(pattern, "", text)

        return text.strip()

    @staticmethod
    def __handle_request_exception(rjcode: str, task: str, err: RequestException):
        if isinstance(err, Timeout):
            # 请求超时
            Renamer.logger.warning(f'[{rjcode}] -> {task}失败[Timeout]：dlsite.com 请求超时！\n')
        elif isinstance(err, ConnectionError):
            # 遇到其它网络问题（如：DNS 查询失败、拒绝连接等）
            Renamer.logger.warning(f'[{rjcode}] -> {task}失败[ConnectionError]：{str(err)}\n')
        elif isinstance(err, HTTPError):
            # HTTP 请求返回了不成功的状态码
            Renamer.logger.warning(
                f'[{rjcode}] -> {task}失败[HTTPError]：{err.response.status_code} {err.response.reason}\n')
        elif isinstance(err, RequestException):
            # requests 引发的其它异常
            Renamer.logger.error(f'[{rjcode}] -> {task}失败[RequestException]：{str(err)}\n')

    @staticmethod
    def getLanguageEdition(rj_code: str):
        api_url = f"https://www.dlsite.com/maniax/api/=/product.json?workno={rj_code.upper()}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Referer": f"https://www.dlsite.com/maniax/work/=/product_id/{rj_code}.html"
        }

        try:
            response = requests.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            return {
                'Japanese': None,
                'Simplified_Chinese': None,
                'Traditional_Chinese': None,
                'error': f"API请求失败: {str(e)}"
            }

        # 初始化结果
        result = {
            'Japanese': None,
            'Simplified_Chinese': None,
            'Traditional_Chinese': None,
            'error': None
        }

        if not isinstance(data, list) or len(data) == 0:
            return {**result, 'error': "无效的RJ号或数据格式异常"}

        main_work = data[0]

        # 解析多语言版本信息
        if 'language_editions' in main_work:
            current_workno = main_work['workno']
            editions = main_work['language_editions']

            # 创建版本映射表
            lang_map = {
                'JPN': 'Japanese',
                'CHI_HANS': 'Simplified_Chinese',
                'CHI_HANT': 'Traditional_Chinese'
            }

            # 构建完整的版本列表（包含自身）
            all_editions = [ed for ed in editions if ed['workno'] == current_workno] + editions

            # 去重处理
            seen = set()
            unique_editions = []
            for ed in all_editions:
                if ed['workno'] not in seen:
                    seen.add(ed['workno'])
                    unique_editions.append(ed)

            # 填充结果
            for edition in unique_editions:
                lang_code = edition['lang']
                if lang_code in lang_map:
                    result[lang_map[lang_code]] = edition['workno']

        # 特殊处理中文版本反向查找日文原版
        if not result['Japanese'] and any([result['Simplified_Chinese'], result['Traditional_Chinese']]):
            original_workno = main_work.get('translation_info', {}).get('original_workno')
            if original_workno:
                result['Japanese'] = original_workno

        return result

    def rename(self, root_path: str):
        work_folders = self.__scaner.scan(root_path)
        for rjcode, folder_path in work_folders:
            Renamer.logger.info(f'[{rjcode}] -> 发现 RJ 文件夹："{os.path.normpath(folder_path)}"')
            dirname, basename = os.path.split(folder_path)
            # 获取不同语言版本
            language_edition = Renamer.getLanguageEdition(rjcode)
            prefer_rj = rjcode
            prefer_title = rjcode
            if self.__rjcode_language_order:
                for key in self.__rjcode_language_order:
                    rj = language_edition.get(key)
                    if rj is not None:
                        prefer_rj = rj
                        break
                else:
                    Renamer.logger.error(f'[{rjcode}] -> ：{str(language_edition.get("error"))}\n')

            if self.__title_language_order:
                for key in self.__title_language_order:
                    rj = language_edition.get(key)
                    if rj is not None:
                        prefer_title = rj
                        break
                else:
                    Renamer.logger.error(f'[{rjcode}] -> ：{str(language_edition.get("error"))}\n')

            # 爬取元数据
            try:
                metadata = self.__scraper.scrape_metadata(prefer_title)
                metadata['rjcode'] = prefer_rj
                # 解决翻译版本社团名为大家翻的问题
                if language_edition["Japanese"] and prefer_title is not language_edition["Japanese"]:
                    jap_metadata = self.__scraper.scrape_metadata(language_edition["Japanese"])
                    metadata['maker_name'] = jap_metadata['maker_name']
            except RequestException as err:
                Renamer.__handle_request_exception(rjcode, '爬取元数据', err)  # 爬取元数据失败
                continue

            # 修改封面
            if self.__make_folder_icon:
                try:
                    icon_name, _ = Renamer.changeIcon(self, rjcode, metadata['cover_url'], folder_path)  # 修改封面
                except RequestException as err:
                    Renamer.__handle_request_exception(rjcode, '下载封面图', err)  # 下载封面图失败
                    continue
                except OSError as err:
                    Renamer.logger.error(f'[{rjcode}] -> 修改封面失败[OSError]：{str(err)}\n')
                    continue

            # 重命名文件夹
            new_basename = self.__compile_new_name(metadata)
            new_folder_path = os.path.join(dirname, new_basename)
            try:
                os.rename(folder_path, new_folder_path)
                Renamer.logger.info(f'[{rjcode}] -> 重命名成功："{os.path.normpath(new_folder_path)}"\n')
                return new_folder_path
            except FileExistsError as err:
                filename = os.path.normpath(err.filename)
                filename2 = os.path.normpath(err.filename2)
                Renamer.logger.warning(
                    f'[{rjcode}] -> 重命名失败[FileExistsError]：{err.strerror}："{filename}" -> "{filename2}"\n')
                return
            except OSError as err:
                Renamer.logger.error(f'[{rjcode}] -> 重命名失败[OSError]：{str(err)}\n')
                return

                # 修改文件夹封面

    def changeIcon(self, rjcode: str, cover_url: str, icon_dir: str):
        os.chmod(icon_dir, stat.S_IREAD)
        icon_name, jpg_name = self.__scraper.scrape_icon(rjcode, cover_url, icon_dir)

        ini_file_path = Path(os.path.join(icon_dir, "desktop.ini"))
        if not os.path.exists(ini_file_path):
            # 编写 desktop.ini
            iniline1 = "[.ShellClassInfo]"
            iniline2 = "IconResource=" + "\"" + icon_name + "\"" + ",0"
            iniline3 = "[ViewState]" + "\n" + "Mode=" + "\n" + "Vid=" + "\n" + "FolderType=StorageProviderGeneric"
            iniline = iniline1 + "\n" + iniline2 + "\n" + iniline3

            # 写入 desktop.ini
            with open(ini_file_path, "w", encoding='utf-8') as inifile:
                inifile.write(iniline)
                inifile.close()

            # 隐藏 desktop.ini 文件 & .ico 文件
            win32api.SetFileAttributes(str(ini_file_path), 38)
            win32api.SetFileAttributes(os.path.join(icon_dir, icon_name), 38)
            # cmd1 = icon_dir[0:2]
            # cmd2 = "cd " + '\"' + icon_dir + '\"'
            # cmd3 = "attrib +h +s " + 'desktop.ini'
            # cmd4 = "attrib +h +s " + icon_name
            # cmd = cmd1 + " & " + cmd2 + " & " + cmd3 + " & " + cmd4
            # os.system(cmd)  # 运行 cmd
            Renamer.logger.info(f'[{rjcode}] -> 修改封面成功："{icon_name}"')

        if self.__remove_jpg_file:
            # 删除 .jpg 文件
            jpg_path = Path(os.path.join(icon_dir, jpg_name))
            jpg_path.unlink(missing_ok=True)

        return icon_name, jpg_name
