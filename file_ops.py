import difflib
import os
import re

import chardet as chardet

import pk_logger

logger = pk_logger.Pk_logger('file_ops_logger', 'log.txt').add_log_handler().get_logger()

def mk_if_not_exit(path):  # 若文件夹不存在则创建
    if not os.path.exists(path):
        os.makedirs(path)


def is_volume_zip(file_name):  # 判断是否是分卷压缩

    if not os.path.exists(file_name):
        return False
    pattern_7z = r"(.*)\.\d{3}\b"  # 7z分卷： [basename].001,[basename].002 ...
    pattern_rar = r"(.*)\.part\d+"  # rar分卷： [basename].part1.[extension],[basename].part2.[extension] ...
    pattern_zip = r"(.*)\.z\d{2}\b"  # zip分卷： [basename].zip,[basename].z01,[basename].z02 ...

    if re.search(r"(.*)\.zip\b", file_name):
        father, name = os.path.split(file_name)
        basename, _ = os.path.splitext(name)
        next_volume = os.path.join(father, basename)
        next_volume = next_volume + ".z01"
        return os.path.exists(next_volume)

    return bool(re.search(pattern_7z, file_name)) or bool(re.search(pattern_rar, file_name)) or bool(
        re.search(pattern_zip, file_name))


# 找到属于同分卷压缩包的所有分卷
def volume_zip_list(file_path):
    dirname = os.path.split(file_path)[0]
    files = os.listdir(dirname)  # 分卷压缩包所在文件夹
    basename = os.path.basename(file_path)  # 分卷压缩包文件名

    # 使用文件夹正则找到分卷压缩包，并捕获分卷无后缀的文件名
    pattern_7z = r'(.*)\.\d{3}\b'
    pattern_rar = r'(.*)\.part\d+'
    pattern_zip = r'(.*)\.z[i\d][p\d]\b'
    re_7z = re.search(pattern_7z, basename)
    re_rar = re.search(pattern_rar, basename)
    re_zip = re.search(pattern_zip, basename)
    # 使用捕获到的文件名改写正则
    if re_7z:
        filename = re.escape(re_7z.group(1))
        pattern = r'{}\.\d{{3}}\b'.format(filename)  # 用于捕获分卷标识（如.001，.002）前的名称
    elif re_rar:
        filename = re.escape(re_rar.group(1))
        pattern = r'{}\.part\d+'.format(filename)  # 标识如.part1,.part2
    elif re_zip:
        filename = re.escape(re_zip.group(1))
        pattern = r'{}\.z[i\d][p\d]\b'.format(filename)
    else:
        return  # 7z和rar和zip的分卷命名正则都无法命中

    # 使用改写后的正则寻找同属的分卷
    zip_list = []
    for file in files:
        match = re.search(pattern, file)
        if match:
            path = os.path.join(dirname, file)
            if not file == match.group():
                new_path = os.path.join(dirname, match.group())
                os.renames(path, new_path)
                logger.info('修改分卷名为7zip易识别格式[ {} ] -> [ {} ]'.format(path, new_path))
                path = new_path
            zip_list.append(path)
    return zip_list


def encode_detect(str_name):
    # 分别尝试用GBK和UTF8解码文件名
    try:
        encode_name = str_name.encode('gbk')
    except UnicodeEncodeError:
        encode_name = str_name.encode('utf-8')
    # 检测可能的正确编码
    result = chardet.detect(encode_name)
    if not result['encoding']:
        return True
    return result['encoding'] == 'SHIFT_JIS'


def get_similar(path):  # 获得与输入路径相似文件路径
    if os.path.exists(path + "(1)"):
        return path + "(1)"
    filename, _ = os.path.splitext(path)
    if os.path.exists(filename):
        return filename
    father, name = os.path.split(path)  # 所在文件夹
    files = os.listdir(father)
    max_similar = 0  # 相似度最高值
    result = None
    for file in files:
        file_path = os.path.join(father, file)
        similar = difflib.SequenceMatcher(None, name, file).quick_ratio()
        if similar > 0.9 and similar > max_similar:
            max_similar = similar
            result = file_path
    # 只返回相似路径不返回相同路径
    return result if not result == path else None


def get_similar_path(path):
    path_list = path.split('\\')
    new_path = path_list[0] + '\\'
    for item in path_list[1:]:
        temp = os.path.join(new_path, item)
        if '?' not in item:
            new_path = temp

        similar = get_similar(temp)
        if similar:
            new_path = similar

    return new_path if not new_path == path else None


# 找到套娃文件夹最里面的文件夹
def last_dir(path):
    dirs = os.listdir(path)
    if len(dirs) == 1:
        new_path = os.path.join(path, dirs[0])
        if os.path.isdir(new_path):
            return last_dir(new_path)
    return path
