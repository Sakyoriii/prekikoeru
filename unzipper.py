import logging
import multiprocessing
import os
import re

from multiprocessing import Process

import file_ops
from seven_z_driver import SevenZDriver, JapDecodeError, GetNamelistError, NoFile2ProcessError

from zip import Zip


class Unzipper():

    def __init__(self, logger, progress_ui):
        self.logger = logger
        self.progress_ui = progress_ui

    def load_namelist(self, zip: Zip):
        passwords = zip.pw_list
        namelist = []
        driver = SevenZDriver()
        if not zip.volumes:
            zip.volumes = [zip.path]
        for volume in zip.volumes:
            driver.set_compress_file(volume)
            for password in passwords:
                driver.set_password(password)
                try:
                    volume_namelist = driver.get_namelist()
                except GetNamelistError as err:
                    if zip.extension in ['.mp4', '.mkv']:
                        zip.covered = True
                        driver.set_covered(True)
                        volume_namelist = driver.get_namelist()
                    elif 'Wrong password' in err.error_info:
                        continue
                    else:
                        self.logger.error(err.error_info)
                        break
                except JapDecodeError:
                    zip.jap = True
                    driver.set_jap(True)
                    volume_namelist = driver.get_namelist()
                if volume_namelist:
                    namelist.extend(volume_namelist)
                    start_at = passwords.index(password)
                    passwords = passwords[start_at:]
                    break
            else:
                break
        if len(namelist) > 0:
            zip.pw_list = passwords
            namelist = list(set(namelist))
            if len(namelist) == 1:
                rj = re.compile(r'[RBV]J(\d{6}|\d{8})(?!\d+)').search(namelist[0].upper())
                if rj:
                    passwords.insert(0, rj.group())
            zip.file_list = namelist
            return True
        return False

    def unzip(self, zip: Zip, output_path, thread_size):
        size = 0
        if zip.volumes:
            for volume in zip.volumes:
                size += os.path.getsize(volume) / (1024 * 1024)
        # else:
        #     size = os.path.getsize(zip.path) / (1024 * 1024)
        self.logger.debug('尝试解压[{}]'.format(zip.path))
        try:
            password = self.password_collision(zip, output_path, thread_size)
        except NoFile2ProcessError:
            self.logger.debug('文件[{}]中含有特殊字符无法逐个解压，使用单进程完整解压'.format(zip.path))
            if not self.single_threaded_unzip(zip, output_path):
                return None
        else:
            if not password:
                self.logger.info(f" 文件[' {zip.path} ']解压失败,无匹的解压码")
                return None
            elif len(zip.file_list) == 1 or zip.covered:
                self.logger.info(f" 文件[' {zip.path} ']解压完成")
            elif size / len(zip.file_list) > 25.6:  # 由于前置过滤的存在，计算并不完全准确
                self.logger.info(f" 使用多线程解压 [' {zip.path} ']")
                self.multi_threaded_unzip(zip, output_path, thread_size, self.progress_ui)
                self.logger.info(f" 文件[' {zip.path} ']解压完成")
            else:
                self.logger.info(f" 小文件较多（{size}MB/{len(zip.file_list)}Files），使用单线程解压 [' {zip.path} ']")
                if not self.single_threaded_unzip(zip, output_path):
                    return None
        return output_path

    def password_collision(self, zip: Zip, output_path, thread_size):
        multi_threading = False
        result_list = multiprocessing.Manager().list([7] * thread_size)
        first_file = '2.zip' if zip.covered else zip.file_list[0]
        index = 0
        threads = [False] * thread_size
        for password in zip.pw_list:
            index = (index + 1) % thread_size
            if not multi_threading:
                unzip_thread(zip, first_file, password, output_path, result_list, 0)
                returncode, msg = result_list[0]
                if returncode == 0:
                    zip.pw_list = [password]
                    return password
            else:
                if threads[index]:
                    if threads[index].is_alive():
                        threads[index].join()
                    returncode, msg = result_list[index]
                    if returncode == 0:
                        return threads[index].name

                p = Process(name=password, target=unzip_thread,
                            args=(zip, first_file, password, output_path, result_list, index))
                p.start()
                threads[index] = p

        index = 0
        for p in threads:
            if p:
                p.join()
                returncode, msg = result_list[index]
                if returncode == 0:
                    zip.pw_list = [password]
                    return password
            index += 1
        return None

    def multi_threaded_unzip(self, zip: Zip, output_path, thread_size, porgress_ui):
        index = 0  # 进程索引
        process = [False] * thread_size
        result_list = multiprocessing.Manager().list([7] * thread_size)
        result = 0  # 进程结果
        progress = 1  # 进度
        file_list = zip.file_list
        password = zip.pw_list[0]
        for file in file_list[1:]:
            porgress_ui.update_progress(progress, len(file_list), '{} : {}'.format(zip.path, file))
            if len(file_list) == 1:
                file = None

            # 循环等等空进程
            while True:
                # if index == thread_size - 1:
                #     time.sleep(0.1)
                try:
                    p = process[index]
                except IndexError:
                    p = False

                if not p or not p.is_alive():
                    break
                index = (index + 1) % thread_size

            # 发现空线程，创建任务
            if p:
                result, msg = result_list[index]
                if not result == 0:
                    print(msg)
                    break

            p = Process(target=unzip_thread,
                        args=(zip, file, password, output_path, result_list, index))
            p.start()
            process[index] = p
            progress += 1

        else:
            # 等待所有进程结束
            print('等待所有解压进程结束...')
            for p in process:
                if p:
                    p.join()
            # if len(file_list)-1<
            # for result, msg in result_list:
            #     if not result == 0:
            #         self.logger.info(f" 文件[' {zip.path} ']解压失败,{msg}")
            #     return
            self.logger.info(
                f"解压完成： [' {zip.path} '] 使用密码： [' {password} '] ,删除压缩文件：'{zip.del_after_unzip}")
            porgress_ui.update_progress(progress, len(file_list), '完成')

        if not result == 0:
            self.logger.info(f" 文件[' {zip.path} ']解压失败,{msg}")

    def single_threaded_unzip(self, zip: Zip, output_path):
        driver = SevenZDriver().set_compress_file(zip.path).set_output_path(output_path).set_jap(zip.jap).set_covered(
            zip.covered)
        for password in zip.pw_list:
            returncode, msg = driver.set_password(password).unzip()
            if returncode == 0:
                self.logger.info(f'[{zip.path}]解压完成')
                return True
        else:
            self.logger.info(f" 文件[' {zip.path} ']密码匹配失败")
            return False

    def find_zip(self, path, passwords, delete_after_unzip, already_add: list, zip_list: list):
        self.logger.debug('检查:' + path)
        # 路径是文件夹，扫描一层，只检查文件
        # 分卷只添加一次避免被反复添加解压
        # 路径不存在或无法识别，尝试相似路径
        if not os.path.exists(path):
            similar = file_ops.get_similar_path(path)
            if similar:
                self.logger.debug(' 尝试相似路径 [{}]'.format(similar))
                return self.find_zip(similar, passwords, delete_after_unzip, already_add, zip_list)

        if path in already_add:
            return False

        if os.path.isdir(path):
            find = False
            files = os.listdir(path)
            if len(files) > 20:
                return find
            for file in files:
                file = os.path.join(path, file)
                if not os.path.isdir(file):
                    find = self.find_zip(file, passwords, delete_after_unzip, already_add, zip_list) or find
            return find

        zip_entity = Zip(path, passwords, delete_after_unzip)
        # 路径是压缩文件，分卷只把头卷加入队列
        log = None
        if file_ops.is_volume_zip(path):
            # 命名符合分卷压缩正则，把同目录下同属的分卷包装成list
            # 修改统一易识别分卷后缀并返回分卷列表
            volumes = file_ops.volume_zip_list(path)
            zip_entity.path = volumes[0]
            zip_entity.volumes = volumes
            already_add.extend(volumes)
            # zip_list.append(zip_entity)
            log = ' 发现分卷压缩文件： [{}]'.format('],['.join(volumes))

        if self.load_namelist(zip_entity):
            if not log:
                log = ' 发现压缩文件： [{}]'.format(path)

            zip_list.append(zip_entity)
            self.logger.info(log)
            return True

        self.logger.info(' 文件 [{}] 无法识别,请检查文件是否可解压及密码是否匹配'.format(path))
        return False


def unzip_thread(zip: Zip, output_file, password, output_path, result_list, index):
    driver = SevenZDriver().set_compress_file(zip.path).set_output_file(output_file).set_password(
        password).set_output_path(output_path).set_jap(zip.jap).set_covered(zip.covered)
    returncode, msg = driver.unzip()
    # print(msg)
    # if msg:
    #     if "No files to process" in msg:
    #         raise NoFile2ProcessError(msg)
    result_list[index] = (returncode, msg)
