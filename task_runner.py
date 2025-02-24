import copy
import os
import re
import shutil

import config
import password
import dlrenamer.ez_client
import file_ops
import filter
import pk_logger

from file_ops import mk_if_not_exit, logger

from timeline import Timeline, Archive, Record, extend
from unzipper import Unzipper

logger = pk_logger.Pk_logger('task_runner', 'log.txt').add_log_handler().get_logger()
conf = config.Config()
passwords = password.read_password()
unzipper = Unzipper(logger, None)
filter = filter.Filter(conf.filter_kw, conf.filter_dir, logger)
renamer = dlrenamer.ez_client.ez_client()
progress_ui = "not initialized"
already_add = []
timelines = []
done = []


def Log_AOP(func):
    def wrapper(timeline):
        input = timeline.get_current_path()
        output = func(timeline)
        fname = timeline.get_current_record().ops
        logger.info(' [{}]：  [{}] -> [{}]'.format(fname, input, output))
        return output

    return wrapper


def Timeline_AOP(func):
    def wrapper(timeline):
        input = timeline.get_current_record().output_file
        output_path = func(timeline)
        if not output_path:
            # 如果返回None，则不进行任何操作
            return
        ops = func.__name__
        if ops == 'pre_filter':
            output = output_path
        else:
            output = Archive(output_path)
        extend(output, input)
        record = Record(input, ops, output)
        timeline.add_record(record)
        return output_path

    return wrapper


# loop of unzip
# progress:
# 0.find_zip
# 0.1.pre_filter
# 0.2.unzip
# 0.3.unnest
# 1.insert_RJ
# 2.post_filter
# 3.rename


def unzip_loop():
    for index, timeline in enumerate(timelines):
        ops = timeline.records[-1].ops
        if not ops == 'find_zip':
            continue
        # pre filter
        pre_filter(timeline)
        # unzip
        output_path = unzip(timeline)
        if not output_path:
            continue
        # unnest
        new_path = unnest(timeline)
        # find_zip
        zip_list = []
        blacklist = conf.blacklist

        unzipper.find_zip(new_path, password.get_str_passwords(passwords), conf.del_after_reunzip, already_add,
                          zip_list)
        for i, find in enumerate(zip_list):
            for item in blacklist:
                if find.name.endswith(item):
                    zip_list.pop(i)

        if len(zip_list) > 0:
            new_archive = timeline.get_current_record().output_file
            if len(zip_list) == 1:
                extend(zip_list[0], new_archive)
                timeline.add_record(Record(new_archive, 'find_zip', zip_list[0]))
            else:
                done.append(timeline)
                timelines.pop(index)
                for find in zip_list:
                    extend(find, new_archive)
                    t = Timeline(new_archive, 'find_zip', find)
                    timelines.append(t)
        progress_ui.add2lis(timelines)
        # loop
        if len(zip_list) > 0:
            unzip_loop()

        password.write_password(password.sort_passwords(passwords, 0.5))


@Timeline_AOP
def pre_filter(timeline: Timeline):
    zip: zip.Zip = timeline.get_current_record().output_file
    newzip = copy.deepcopy(zip)
    file_list = filter.pre_filter(zip.file_list)
    if file_list:
        newzip.file_list = file_list
        return newzip
    else:
        return None


@Timeline_AOP
def unzip(timeline: Timeline):
    zip: zip.Zip = timeline.get_current_record().output_file
    if conf.output_path not in zip.path:
        output_path = os.path.join(conf.output_path, zip.filename)
    else:
        output_path = os.path.join(zip.father, zip.filename)
        if os.path.exists(output_path):
            output_path = os.path.join(zip.father, "prekikoeru")
            output_path = os.path.join(output_path, zip.filename)
            # 文件路径
    if zip.RJ_code and zip.RJ_code not in zip.path:
        output_path += zip.RJ_code
    if not unzipper.unzip(zip, output_path, conf.max_thread):
        return
    password.hit_password(passwords, zip.pw_list[0])
    # delete_after_unzip or delete_after_reunzip
    if zip.del_after_unzip:
        for volume in zip.volumes:
            delete_file(volume)
    return output_path


def insert_rj_loop():
    for timeline in timelines:
        insert_RJ(timeline)
        progress_ui.add2lis(timelines)


#  套娃文件夹
@Log_AOP
@Timeline_AOP
def unnest(timeline: Timeline):
    path = timeline.get_current_path()
    # 向前找到最外层文件夹，直至OUTPUT
    rel = os.path.relpath(path, conf.output_path)
    rel_path = rel.split('\\')
    first = os.path.join(conf.output_path, rel_path[0])
    # 由最外箱内找到最后一个套娃文件夹
    last = file_ops.last_dir(first)
    print('checkTW -- first :{} , last :{} '.format(first, last))
    rel = os.path.relpath(last, conf.output_path)
    rel_path = rel.split('\\')
    # 若最后一个文件夹名不包含Rj，则从相对路径中或RJ参数中补充Rj
    # new_path = path
    if len(rel_path) > 1:
        try:
            for item in os.listdir(last):
                src_path = os.path.join(last, item)
                dest_path = os.path.join(first, item)

                # 移动文件和文件夹
                shutil.move(src_path, dest_path)
                # shutil.move(last, conf.output_path)

        except shutil.Error as err:
            logger.error(err)
            # os.rename(last, last + '(1)')  # 小而美的防重方案
            # last += '(1)'
            # shutil.move(last, conf.output_path)

        # dest = os.path.join(conf.output_path, rel.split('\\')[0])
        try:
            os.rmdir(last)
        except Exception as ex:
            print("错误信息：" + str(ex))  # 提示：错误信息，目录不是空的
        # basename = last.split('\\')[-1]
        # new_path = os.path.join(conf.output_path, basename)
        # timeline.add_record(timeline.get_current_record().output_file, conf.already_add, 1)
        # new_archive = Archive(new_path)
        # timeline.get_current_record().output_file = new_archive
        # logger.info(' 移除套娃文件夹： [{}] -> [{}]'.format(last, new_path))
    return first


@Log_AOP
@Timeline_AOP
def insert_RJ(timeline: Timeline):
    pattern = r'[RBV]J(\d{6}|\d{8})(?!\d+)'
    file_name = timeline.get_current_record().output_file.path
    if not re.compile(pattern).search(file_name.upper()):
        archives = timeline.get_all_input_archives()
        archives.extend(timeline.get_all_output_archives())
        for archive in archives:
            try:
                rj = archive.RJ_code
            except AttributeError:
                rj = re.compile(pattern).search(archive.name.upper())
                rj = None if not rj else rj.group()
            if rj:
                break
        else:
            return

        old_path = timeline.get_current_path()
        new_path = old_path + '-' + rj
        os.rename(old_path, new_path)
        return new_path
        # new_archive = Archive(new_path)
        # timeline.add_record(Record(Archive(timeline.get_current_path()), 'insert_RJ', new_archive))
        # logger.info(' 文件夹重命名插入RJ：  [{}] -> [{}]'.format(old_path, new_path))


def filter_loop():
    for timeline in timelines:
        post_filter(timeline)
        progress_ui.add2lis(timelines)


@Timeline_AOP
def post_filter(timeline: Timeline):
    input = timeline.get_current_path()
    hit = filter.post_filter(input)
    return input if hit else None


def rename_loop():
    for timeline in timelines:
        rename(timeline)
    progress_ui.add2lis(timelines)
    for t in done:
        logger.info(t)
    for t in timelines:
        logger.info(t)


@Timeline_AOP
def rename(timeline: Timeline):
    path = timeline.get_current_path()
    # 走到这里时的路径可能是子文件夹，从子文件夹到输出路径中取出最外层文件夹
    rel = os.path.relpath(path, conf.output_path)
    father = os.path.join(conf.output_path, rel.split('\\')[0])
    new_path = renamer.run_renamer(father)
    return new_path


def create_timeline(files, in_progress, progres_ui=progress_ui):
    if in_progress == 0:
        for file in files:
            zip_list = []
            if unzipper.find_zip(file, password.get_str_passwords(passwords), conf.del_after_unzip, already_add,
                                 zip_list):
                for zip in zip_list:
                    timeline = Timeline(Archive(file), 'find_zip', zip)
                    timelines.append(timeline)
    else:
        for file in files:
            archive = Archive(file)
            timeline = Timeline(archive, 'create_timeline', archive)
            timelines.append(timeline)
    # elif in_progress == 2:
    #     for file in files:
    #         timeline = Timeline(Archive(file), 'post_filter')
    #         filter.post_filter(file)
    #         timeline.add_output_path(file)
    #         timelines.append(timeline)
    # elif in_progress == 3:
    #     for file in files:
    #         timeline = Timeline(Archive(file), 'rename')
    #         output_list = dlrenamer.ez_client.run_renamer(file)
    #         timeline.add_output_path(output_list)
    #         timelines.append(timeline)
    progress_ui.add2lis(timelines)


# def timelines_runner(task_list: list, progress_ui):
#     for task in task_list:
#         if task == 'unzip':
#             for timeline in timelines:
#                 record = timeline.get_current_record
#                 if record.ops == 'unzip':
#                     unzip_loop(timeline, progress_ui)
#
#     pass


def delete_file(file_path):  # 删除方法，若配置逻辑删除则丢进回收文件夹
    if conf.logical_deletion:
        mk_if_not_exit(conf.recycle_path)
        rel_path = False
        if conf.output_path in file_path:  # 在输出路径中的文件，保留相对路径移动到回收站
            rel_path = os.path.relpath(file_path, conf.output_path)
            rel_recycle = os.path.join(conf.recycle_path, os.path.split(rel_path)[0])
            mk_if_not_exit(rel_recycle)
        try:
            shutil.move(file_path, rel_recycle if rel_path else conf.recycle_path)
        except shutil.Error as err:
            os.remove(file_path)
            logger.error("shutil.Error: {0},use remove instead".format(err))

    else:
        if os.path.isdir(file_path):
            shutil.rmtree(file_path)
        else:
            os.remove(file_path)


def clear():
    timelines.clear()


def reload():
    global conf
    conf = config.Config()
    global passwords
    passwords = password.read_password()
