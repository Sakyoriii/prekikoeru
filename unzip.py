import multiprocessing
import os

import re
import subprocess

import zipfile
from multiprocessing import Process

import filetype

import main
import file_ops
import pk_logger
from timeline import Archive

logger = pk_logger.Pk_logger('unzip_logger', 'log.txt').add_log_handler().get_logger()


class Zip(Archive):

    def __init__(self, file, password_list: list, del_after_unzip: bool, note: str = None):
        super(Zip, self).__init__(file)
        self.pw_list = password_list
        self.del_after_unzip = del_after_unzip
        self.pw_list.insert(0, self.filename)
        self.RJ_code = None
        # 匹配文件名或备注中Rj号，插入密码表
        self.getRJ(self.name)
        if note:
            self.getRJ(note)
        if self.RJ_code:
            self.pw_list.insert(0, self.RJ_code)

    def getRJ(self, string: str):
        RJ = re.compile(r'[RBV]J(\d{6}|\d{8})(?!\d+)').search(string.upper())
        if RJ:
            self.RJ_code = RJ.group()

    def __str__(self):
        return self.path

    def init_file_list(self):
        file_list, password = get_namelist(self.path, self.pw_list)  # 压缩文件内文件列表
        self.file_list = file_list
        if not file_list:
            return False
        start_at = self.pw_list.index(password)
        self.pw_list = self.pw_list[start_at:]  # 跳过已经校验失败的密码
        return bool(file_list)

    def pre_extract(self):
        for i in range(len(self.file_list)):
            if file_ops.encode_detect(self.file_list[i]):
                break
        else:
            return False
        self.file_list, _ = get_namelist(self.path, self.pw_list, True)
        return True


def is_archive(file):  # 判断是否是压缩文件，只判断常见几种类型足够了
    if not os.path.exists(file):
        logger.error('路径[{}]不存在，请检查路径是否包含错误解码的特殊字符'.format(file))
        return False
    if not os.path.isdir(file):
        archive = ['zip', '7z', 'tar', 'rar', 'gzip']
        guess = filetype.guess(file)
        if guess:
            filetype.archive_matchers
            if guess.extension == 'exe':
                password_list = main.passwords
                full_filename = os.path.basename(file)
                filename = full_filename.split('.')[0]
                password_list.append(filename)
                namelist, _ = get_namelist(file, password_list)
                return bool(list)
            return any(t in guess.mime for t in archive) or guess.extension == 'rar'
    return False


# 处理压缩包的线程函数
def unzip_main():
    while not main.task_queue.empty():
        compress_file: Zip = main.task_queue.get_nowait()  # 解包得到压缩文件路径和是否删除
        # full_filename = os.path.basename(compress_file)  # 完整文件名
        # filename, extension = os.path.splitext(full_filename)  # 文件名，文件扩展名

        pw_list = compress_file.pw_list
        # # 取出密码本到临时密码表，加入文件名
        # pw_list = compress_file.pw_list
        # pw_list.insert(0, filename)
        # # 匹配文件名中Rj号，插入密码表
        # RJ = re.compile(r'[RBV]J(\d{6}|\d{8})(?!\d+)').search(compress_file.upper())
        # if RJ:
        #     pw_list.insert(0, RJ.group())
        # # 获得压缩文件内文件列表
        # file_list, pw = get_namelist(compress_file, pw_list)

        # if not file_list:
        #     logger.info(' 文件[' + compress_file + ']解压失败,无匹的解压码')
        #     continue
        # index = pw_list.index(pw)
        # pw_list = pw_list[index:]

        jap = compress_file.pre_extract()
        if jap:
            logger.info(' 检测到日文乱码，使用： [SHIFT_JIS] 编码尝试解压： [' + compress_file.filename + '] 文件')

        #  前置过滤器
        filtered_list = file_ops.pre_filter(compress_file.file_list)
        #  套娃压缩包在原路径解压，其他解压到output/压缩包名
        if main.output_path not in compress_file.path:
            output_path = os.path.join(main.output_path, compress_file.filename)
        else:
            output_path = compress_file.father  # 文件路径

        # 开始使用7zip解压缩文件
        for password in pw_list:
            index = 0  # 进程索引
            max = main.max_thread
            process = [False] * max
            wait = True
            result_list = multiprocessing.Manager().list([7] * max)
            result = 0  # 进程结果
            progress = 0  # 进度
            wildcard = False  # 使用通配符

            for file in filtered_list:
                pk_logger.gui.update_progress(progress, len(filtered_list), '{} : {}'.format(compress_file, file))
                if len(filtered_list) == 1:
                    file = None

                # 循环等等空进程
                while True:
                    try:
                        p = process[index]
                    except IndexError:
                        p = False

                    if not p or not p.is_alive():
                        break
                    if not wait:
                        index = (index + 1) % max
                    else:
                        pk_logger.gui.update_progress(progress, len(filtered_list),
                                                      '{} : 尝试匹配密码[{}]'.format(compress_file, password))
                # 发现空线程，创建任务
                if p:
                    result = result_list[index]
                    if result == 0:
                        wait = False
                    elif result.__class__ == str and result.startswith("333"):
                        retry = result.split(" ", 1)[1]
                        if wildcard and retry in filtered_list:  # 文件为二次重试
                            file = None
                            logger.debug('文件名{}中含有特殊字符无法逐个解压，使用单进程完整解压'.format(retry))
                        else:
                            # 把失败文件加入到队尾
                            filtered_list.append(retry)
                            # 使用通配符替换特殊字符
                            for i, e in enumerate(filtered_list):
                                # 使用通配符替换所有符号
                                filtered_list[i] = re.sub(r'[〜？！_]', "?", e)
                            file = re.sub(r'[〜？！_]', "?", file)
                            wildcard = True
                            logger.debug('压缩文件{}的文件列表中含未能正确编码的有特殊字符，使用通配符参数，可能造成进度显示错误'.format(retry))
                    else:
                        break

                p = Process(target=try_unzip,
                            args=(compress_file.path, file, password, output_path, jap, index, result_list,))
                p.start()
                process[index] = p
                progress += 1

                if wait:
                    p.join()
                    result = result_list[index]
                    if not file:
                        progress = len(filtered_list)
                        break
            else:
                # 等待所有进程结束
                for p in process:
                    if p:
                        p.join()

            if not result == 0:  # 解压失败，密码错误或其他错误
                continue

            logger.info(f"解压完成： [' {compress_file} '] 使用密码： [' {password} '] ,删除压缩文件：'{compress_file.del_after_unzip}")
            pk_logger.gui.update_progress(progress, len(filtered_list), '完成')
            # 删除已解压的压缩文件
            if compress_file.del_after_unzip:
                if file_ops.is_volume_zip(compress_file.path):
                    for volume in file_ops.volume_zip_list(compress_file.path):
                        file_ops.delete_file(volume)
                else:
                    file_ops.delete_file(compress_file.path)
            # 检查是否套娃并添加到解压队列或过滤文件,整理文件去文件夹套娃
            file_ops.recheck(output_path, compress_file)
            break
        else:
            # 所有密码都尝试失败，将压缩包添加到失败列表
            logger.info(f" 文件[' {compress_file} ']解压失败,无匹的解压码")
        # 刷新ui中未完成list
        pk_logger.gui.add2lisbox(main.task_queue)


def try_unzip(compress_file, file, password, output_path, jap, index, result_list):
    # x 解压  -p 使用密码 -y 重复文件不询问直接覆盖 -o 输出路径 -mcp 编码代码
    cmd = ['7z', 'x', '-p{}'.format(password), '-y', compress_file]
    code = False
    if file:  # 解压压缩包内的指定文件
        cmd.append(file)
        parent = file.split("\\")[0]
        if os.path.join(output_path, parent) == compress_file:
            parent += "(1)"
            output_path = os.path.join(output_path, parent)
    if jap:
        # 使用SHIFT_JIS编码解压
        cmd.append('-mcp=932')

    cmd.append('-o{}'.format(output_path))

    print(cmd)
    result = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    while result.poll() is None:
        output = result.stdout.readlines()
        if output:
            for log in output:
                if "No files to process" in log.strip().decode('gbk'):  # gbk无法正确编码特殊符号导致无法找到要解压的目标文件
                    code = 333
    if result.returncode == 0 and code:
        result_list[index] = f'{code} {file}'
    else:
        result_list[index] = result.returncode
    return result.returncode == 0


# 获取zip压缩文件的文件列表
def get_zip_namelist(file):
    with zipfile.ZipFile(file, 'r') as z:
        namelist = z.namelist()
        return namelist


# 获取7z压缩文件的文件列表
# def get_7z_namelist(file, password_list):
#     for password in password_list:
#         try:
#             with py7zr.SevenZipFile(file, mode='r', password=password) as z:
#                 files = z.getnames()
#                 return files
#         except _lzma.LZMAError as err:
#             print(err)
#             # logger.error(' 文件[' + file + ']可能已损坏')
#             # return
#
#         except py7zr.exceptions.Bad7zFile:
#             pass
#
#     # 所有密码都尝试失败，将压缩包添加到失败列表
#     logger.info(' 文件[' + file + ']解压失败,无匹的解压码')


def get_namelist(file_path, password_list, jap=False):
    pattern = r'^20\d{2}-[01]\d-[0-3]\d [0-2]\d:[0-6]\d:[0-6]\d \.\S{4}.{28}(.+?)\r'
    namelist = []
    for password in password_list:
        cmd = ['7z', 'l', file_path, '-p{}'.format(password)]
        if jap:
            # 使用SHIFT_JIS编码解压
            cmd.append('-mcp=932')
        out, err = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True).communicate()
        if err:
            if 'Cannot open the file as archive' in err.decode('gbk'):
                return None, None
            if 'Wrong password' in err.decode('gbk'):
                continue
        if out:
            index = re.search(r'\.part(\d+)$|\.z(\d{2})$|\.(\d{3})$', file_path)
            for line in out.strip().decode('gbk').split('\n'):
                match = re.search(pattern, line)
                if match:
                    namelist.append(match.group(1))

            if namelist:
                if index:
                    for i in range(1, 4):
                        if index.group(i):
                            int_index = int(index.group(i)) + 1
                            next_volume = str(int_index).zfill(i)
                    next_path = re.sub(r'\d+$', str(next_volume), file_path)
                    if os.path.exists(next_path):
                        append_list, _ = get_namelist(next_path, [password])
                        if append_list:
                            namelist = namelist + append_list
                namelist = list(set(namelist))
                return namelist, password
    return None, None


def pre_extract(file_list):
    # 获取压缩文件目录
    # if zipfile.is_zipfile(file):
    #     file_list = get_zip_namelist(file)
    # else:
    #     file_list = get_7z_namelist(file, password_list)
    for file in file_list:
        if file_ops.encode_detect(file):
            # 检测到日文编码SHIFT_JIS
            jp_list = []
            get_namelist()
            return jp_list, True

    return file_list, False
