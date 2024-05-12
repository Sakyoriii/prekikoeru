import difflib
import os
import queue
import re
import shutil

import chardet as chardet

import dlrenamer.ez_client
import main
import pk_logger
import scraper
import unzip

logger = pk_logger.Pk_logger('file_ops_logger', 'log.txt').add_log_handler().get_logger()


def mk_if_not_exit(path):  # 若文件夹不存在则创建
    if not os.path.exists(path):
        os.makedirs(path)


def delete_file(file_path):  # 删除方法，若配置逻辑删除则丢进回收文件夹
    if main.logical_deletion:
        mk_if_not_exit(main.recycle_path)
        if main.output_path in file_path:  # 在输出路径中的文件，保留相对路径移动到回收站
            rel_path = os.path.relpath(file_path, main.output_path)
            rel_recycle = os.path.join(main.recycle_path, os.path.split(rel_path)[0])
            mk_if_not_exit(rel_recycle)
        try:
            shutil.move(file_path, rel_recycle if rel_path else main.recycle_path)
        except shutil.Error as err:
            logger.error("shutil.Error: {0}".format(err))

    else:
        if os.path.isdir(file_path):
            shutil.rmtree(file_path)
        else:
            os.remove(file_path)


def pre_filter(file_list):
    new_list = []
    for file in file_list:
        for key in main.filter_kw:
            match = re.search(key, file.upper())
            if match:
                logger.info('跳过文件夹: [ {} ] 命中关键词： [ {} ]'.format(file, key))
                break
        else:
            new_list.append(file)
    return new_list


def filter_files(path):
    for root, dirs, files in os.walk(path):
        if dirs and main.filte_dir:
            for dir in dirs:
                for key in main.filter_kw:
                    dir_path = os.path.join(root, dir)
                    match = re.search(key, dir_path.upper())
                    if match:
                        delete_file(dir_path)
                        logger.info('过滤文件夹: [ {} ] 命中关键词： [ {} ]'.format(dir_path, key))
        if files:
            for file in files:
                for key in main.filter_kw:
                    file_path = os.path.join(root, file)
                    match = re.search(key, file_path.upper())
                    if match:
                        delete_file(os.path.join(root, file))
                        logger.info('过滤文件: [ {} ] 命中关键词： [ {} ]'.format(file_path, key))


def filter_main():  # 主过滤方法
    while not main.task_queue.empty():
        path = main.task_queue.get()
        filter_files(path)
        main.next_queue.put(path)


def rename_main():  # 主重命名方法
    path_list = []
    while not main.task_queue.empty():
        # 走到这里时的路径可能是子文件夹，从子文件夹到输出路径中取出最外层文件夹
        file_path = main.task_queue.get()
        rel = os.path.relpath(file_path, main.output_path)
        path = os.path.join(main.output_path, rel.split('\\')[0])
        path_list.append(path)

    dlrenamer.ez_client.run_renamer(path_list)


def is_volume_zip(file_name):  # 判断是否是分卷压缩
    pattern_7z = r"(.*)\.\d{3}\b"  # 7z分卷： [basename].001,[basename].002 ...
    pattern_rar = r"(.*)\.part\d+"  # rar分卷： [basename].part1.[extension],[basename].part2.[extension] ...
    return bool(re.search(pattern_7z, file_name)) or bool(re.search(pattern_rar, file_name))


# 找到属于同分卷压缩包的所有分卷
def volume_zip_list(file_path):
    dirname = os.path.split(file_path)[0]
    files = os.listdir(dirname)  # 分卷压缩包所在文件夹
    basename = os.path.basename(file_path)  # 分卷压缩包文件名

    # 使用文件夹正则找到分卷压缩包，并捕获分卷无后缀的文件名
    pattern_7z = r'(.*)\.\d{3}\b'
    pattern_rar = r'(.*)\.part\d+'
    re_7z = re.search(pattern_7z, basename)
    re_rar = re.search(pattern_rar, basename)
    # 使用捕获到的文件名改写正则
    if re_7z:
        filename = re_7z.group(1)
        pattern = r'{}\.\d{{3}}\b'.format(filename)  # 用于捕获分卷标识（如.001，.002）前的名称
    elif re_rar:
        filename = re_rar.group(1)
        pattern = r'{}\.part\d+'.format(filename)  # 标识如.part1,.part2
    else:
        return  # 7z和rar的分卷命名正则都无法命中

    # 使用改写后的正则寻找同属的分卷
    zip_list = []
    for file in files:
        match = re.search(pattern, file)
        if match:
            path = os.path.join(dirname, file)
            if not file == match.group():
                new_path = os.path.join(dirname, match.group())
                os.renames(path, new_path)
                path = new_path
                logger.info('修改分卷名为7zip易识别格式[ {} ] -> [ {} ]'.format(path, new_path))
            zip_list.append(path)
    return zip_list


def merge_zip(compress_file):  # 合并分卷文件
    basename = os.path.basename(compress_file)  # 文件名
    filename = basename.split('.')[0]  # 去掉分卷后缀的文件名

    path = os.path.split(compress_file)[0]  # 文件路径

    # all_file = os.listdir(path)  # 获取路径下所有文件
    # volume = list(filter(lambda f: filename in f and is_volume_zip(f), all_file))  # 过滤，获取所有分卷
    # volume_path_list = []
    volumes = volume_zip_list(compress_file)
    output_path = os.path.join(path, filename)  # 合并后输出路径
    if os.path.exists(output_path):  # 合并文件已存在或重名
        output_path = output_path + '(1)'  # 致敬小而美的重名解决方案
    with open(output_path, 'ab') as outfile:  # append in binary mode
        for volume in volumes:
            # volume_path = os.path.join(path, name)
            # volume_path_list.append(volume_path)

            with open(volume, 'rb') as infile:  # open in binary mode also
                outfile.write(infile.read())

    if main.del_after_merged:  # 合并后删除原来的分卷压缩包
        for volume in volumes:
            delete_file(volume)
    main.task_queue.put((output_path, main.del_after_merged_and_unzip))
    logger.info(' 合并分卷压缩文件： [' + ','.join(volumes) + '] -> [' + filename + '] , 删除分卷文件：' + str(main.del_after_merged))
    return filename


def encode_detect(str_name):
    # 分别尝试用GBK和UTF8解码文件名
    try:
        encode_name = str_name.encode('gbk')
    except UnicodeEncodeError:
        encode_name = str_name.encode('utf-8')
    # 检测可能的正确编码
    result = chardet.detect(encode_name)
    return result['encoding'] == 'SHIFT_JIS'


def scan_file(path, delete):
    print('扫描路径' + str(path))
    # 遍历路径
    for file in os.listdir(path):
        if not os.path.isdir(file):
            find_zip(path, delete)
    # for root, dirs, files in os.walk(path):
    #     if files:
    #         for file in files:
    #             file_path = os.path.join(root, file)
    #             # 扫描到的所有文件加入解压队列
    #             find_zip(file_path, delete)
    #
    #     if dirs:
    #         for dir in dirs:
    #             file_path = os.path.join(root, dir)
    #             # filter_files(file_path)
    #             main.filter_queue.put(file_path)


def recheck(file_list, path):
    print(file_list)
    pattern = r'^(?:[^\\]*|.*?(?=\\))'
    dir_set = set()
    for name in file_list:
        # 在file list中找出压缩文件的所有根目录，使用set集合防重
        dir_set.add(re.search(pattern, name).group())

    for file in dir_set:
        # 遍历根路径(解压文件的第一层目录)，文件夹过滤，压缩文件解套
        file_path = os.path.join(path, file)
        # 只有文件夹才需要去文件夹套娃和更名
        if os.path.isdir(file_path):
            if len(dir_set) == 1:
                # 去文件夹套娃
                file_path = rm_taowadir(file_path)
        else:
            # 检查是不是（套娃）压缩包，是则加入解压任务队列
            find_zip(file_path, main.del_after_reunzip)
        # 过滤文件夹内文件
        main.next_queue.put(file_path)


def find_zip(path, delete):
    # print('检查:' + file)
    logger.debug('检查:' + path)
    # 路径是文件夹，扫描一层，只检查文件
    if os.path.isdir(path):
        for file in os.listdir(path):
            file = os.path.join(path, file)
            if not os.path.isdir(file):
                find_zip(file, delete)
    # 路径是压缩文件，分卷只把头卷加入队列
    elif unzip.is_archive(path):
        if is_volume_zip(path):
            # 分卷只添加一次避免被反复添加解压
            if not ('part1' or '001') in os.path.basename(path):
                return
                # 命名符合分卷压缩正则，把同目录下同属的分卷包装成list
            # merged = merge_zip(path)
            volumes = volume_zip_list(path)
            main.task_queue.put((volumes[0], delete))
            logger.info(' 发现分卷压缩文件： [{}]'.format('],['.join(volumes)))
        else:
            main.task_queue.put((path, delete))
            logger.info(' 发现压缩文件： [{}]'.format(path))
    else:   # 路径不存在或无法识别，尝试相似路径
        similar = get_similar_path(path)
        if similar and not path == similar:
            logger.debug(' 尝试相似路径 [{}]'.format(similar))
            find_zip(similar, delete)
        else:
            logger.debug(' 文件 [{}] 无法识别'.format(path))


def get_similar(path):  # 获得与输入路径相似文件路径
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
    return result


def get_similar_path(path):
    path_list = path.split('\\')
    new_path = ''
    for item in path_list:
        temp = os.path.join(new_path, item)
        if '?' not in item:
            new_path = temp
        else:
            similar = get_similar(temp)
            if similar:
                new_path = similar
            else:
                return None
    return new_path


# 从文件名中匹配RJ号
def find_RJ(path):
    for root, dirsname, files in os.walk(path):
        if dirsname:
            for dir in dirsname:
                RJ = scraper.Dlsite.parse_workno(dir)
                if RJ:
                    return RJ
    return None


# 找到套娃文件夹最里面的文件夹
def last_dir(path):
    dirs = os.listdir(path)
    if len(dirs) == 1:
        new_path = os.path.join(path, dirs[0])
        if os.path.isdir(new_path):
            return last_dir(new_path)
    return path


#  套娃文件夹
def rm_taowadir(path):
    # 向前找到最外层文件夹，直至OUTPUT
    rel = os.path.relpath(path, main.output_path)
    rel_path = rel.split('\\')
    first = os.path.join(main.output_path, rel_path[0])
    # 由最外箱内找到最后一个套娃文件夹
    last = last_dir(first)
    rel = os.path.relpath(last, main.output_path)
    rel_path = rel.split('\\')
    if len(rel_path) > 1:
        rj = re.compile(r'[RBV]J(\d{6}|\d{8})(?!\d+)').search(rel.upper())
        if rj:
            new_path = path + '-' + rj.group()
            os.renames(path, new_path)
            logger.info(' 移除套娃文件夹前重命名保留RJ： [' + path + '] -> [' + new_path + ']')
            path = new_path

        shutil.move(path, main.output_path)
        basename = new_path.split('\\')[-1]
        path = os.path.join(main.output_path, basename)
        shutil.rmtree(os.path.join(main.output_path, rel.split('\\')[0]))
        logger.info(' 移除套娃文件夹： [' + path + '] -> [' + main.output_path + '\\' + path)
    return path
