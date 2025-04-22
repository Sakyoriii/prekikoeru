import os
import re

from enum import Enum

import file_ops
import gui
from seven_z_driver import SevenZDriver, JapDecodeError, GetNamelistError, NoFile2ProcessError, CannotDeleteOutputFile
from unzip_process_pool import ProcessResourceManager

from zip import Zip


class Prefix(Enum):
    PASSWORD_COLLISION = 'PC_'
    UNZIP = 'unzip_'


class Unzipper():

    def __init__(self, logger, resource_manager: ProcessResourceManager, seven_z_path=None):
        self.logger = logger
        # self.progress_ui = progress_ui
        # if seven_z_path is not None:
        #     self.seven_z_path = seven_z_path
        # else:
        #     self.seven_z_path = r'C:\Program Files\7-Zip\7z.exe'

        self.driver = SevenZDriver(seven_z_path) if seven_z_path else SevenZDriver()

        self.resource = resource_manager

    def load_namelist(self, zip: Zip):
        passwords = zip.pw_list
        namelist = []
        compression_ratio_info = {}
        if not zip.volumes:
            zip.volumes = [zip.path]
        for volume in zip.volumes:
            # driver.set_compress_file(volume)

            for password in passwords:
                # driver.set_password(password)
                retry = True
                wrong_password = False
                volume_namelist = []
                while retry:
                    try:
                        volume_namelist, compression_ratio_info = self.driver.get_namelist(compress_file=volume,
                                                                                           password=password,
                                                                                           jap=zip.jap,
                                                                                           covered=zip.covered)
                    except GetNamelistError as err:
                        if zip.extension in ['.mp4', '.mkv']:
                            zip.covered = True
                        elif 'Wrong password' in err.error_info:
                            wrong_password = True
                            break
                        else:
                            self.logger.error(err.error_info)
                            retry = False
                            break
                    except JapDecodeError:
                        zip.jap = True
                    else:
                        break
                if wrong_password:
                    continue
                if not retry:
                    break
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
            zip.compression_ratio_info = compression_ratio_info
            return True
        return False

    def unzip(self, zip: Zip, output_path, thread_threshold_mb, thread_compression_ratio):
        size = 0
        if zip.volumes:
            for volume in zip.volumes:
                size += os.path.getsize(volume) / (1024 * 1024)
        # else:
        #     size = os.path.getsize(zip.path) / (1024 * 1024)
        self.logger.debug('尝试解压[{}]'.format(zip.path))
        try:
            password = self.password_collision(zip, output_path)
            # password = self.quick_password_collision(zip, output_path, True, 1)
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
            elif not zip.compression_ratio_info["encrypted"] and \
                    (size / len(zip.file_list) > 200 or (size / len(zip.file_list) > thread_threshold_mb and zip.compression_ratio_info[
                         "compression_ratio"] > thread_compression_ratio)):  # 判断压缩文件加密、平均文件size、文件压缩率
                # 由于前置过滤的存在，计算并不完全准确
                self.logger.info(f" 使用多线程解压 [' {zip.path} ']")
                if not self.multi_threaded_unzip(zip, output_path):
                    return None
                self.logger.info(f" 文件[' {zip.path} ']解压完成")
            else:
                self.logger.info(f"{size}MB/{len(zip.file_list)} Files "
                                 f"压缩率： {zip.compression_ratio_info.get('compression_ratio')} "
                                 f"加密： {zip.compression_ratio_info.get('encrypted')} ,"
                                 f"使用单线程解压 [' {zip.path} ']")
                if not self.single_threaded_unzip(zip, output_path):
                    return None
        return output_path

    def password_collision(self, zip: Zip, output_path):
        first_file = '2.zip' if zip.covered else zip.file_list[0]
        for password in zip.pw_list:
            args = [zip.path, output_path, password, first_file, zip.jap, zip.covered]
            returncode, msg = self.driver.unzip(*args)
            if returncode == 0:
                zip.pw_list = [password]
                return password

    def multi_threaded_unzip(self, zip: Zip, output_path):
        list_id = Prefix.UNZIP.value + zip.name
        file_list = zip.file_list
        password = zip.pw_list[0]
        self.resource.set_list_total(list_id, len(file_list))
        progress = 1
        for file in file_list[1:]:
            args = [zip.path, output_path, password, file, zip.jap, zip.covered]

            self.resource.submit(list_id, self.driver.unzip, *args)
            self.logger.info(f"提交解压任务至进程池：{file} | {progress}/{len(file_list)} ")
            progress += 1
        else:
            # 阻塞等待该任务组完成
            progress = self.resource.list_progress[list_id]
            self.logger.info(f"等待解压进程 | {progress}/{len(file_list)} ")
            event = self.resource.list_events[list_id]
            event.wait()
            progress = self.resource.list_progress[list_id]
            self.logger.info(f"等待解压进程 | {progress}/{len(file_list)} ")
            status = self.resource.list_status[list_id]
            if status['completed']:
                self.logger.info(
                    f"解压完成： [' {zip.path} '] 使用密码： [' {password} '] ,删除压缩文件：'{zip.del_after_unzip}")
                self.logger.info(f"完成 | {len(file_list)}/{len(file_list)} ")
                return True
            else:
                self.logger.info(f" 文件[' {zip.path} ']解压失败,{status['error']}")
                return False

    def single_threaded_unzip(self, zip: Zip, output_path):
        for password in zip.pw_list:
            returncode, msg = self.driver.unzip(zip.path, output_path, password, None, zip.jap, zip.covered)
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


def unzip_thread(zip: Zip, driver: SevenZDriver, output_file, password, output_path, result_list, index):
    returncode, msg = driver.unzip(zip.path, output_path, password, output_file, zip.jap, zip.covered)
    result_list[index] = (returncode, msg)
