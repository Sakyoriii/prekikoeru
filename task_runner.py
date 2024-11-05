import copy
import os
import re
import shutil

import config
import dlrenamer.ez_client
import file_ops
import filter
import pk_logger
import zip
from file_ops import mk_if_not_exit, logger
from seven_z_driver import SevenZDriver
from timeline import Timeline, Archive, Record
from unzipper import Unzipper

logger = pk_logger.Pk_logger('task_runner', 'log.txt').add_log_handler().get_logger()
conf = config.Config()
filter = filter.Filter(conf.filter_kw, conf.filter_dir, logger)
unzipper = Unzipper(SevenZDriver(), logger)
already_add = []
timelines = []
done = []


#  套娃文件夹
def rm_taowadir(path):
    # path = timeline.get_current_record().output_file.path
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
    new_path = None
    if len(rel_path) > 1:
        try:
            shutil.move(last, conf.output_path)
        except shutil.Error as err:
            logger.error(err)
            os.rename(last, last + '(1)')  # 小而美的防重方案
            last += '(1)'
            shutil.move(last, conf.output_path)

        dest = os.path.join(conf.output_path, rel.split('\\')[0])
        shutil.rmtree(dest)
        basename = last.split('\\')[-1]
        new_path = os.path.join(conf.output_path, basename)
        # timeline.add_record(timeline.get_current_record().output_file, conf.already_add, 1)
        # new_archive = Archive(new_path)
        # timeline.get_current_record().output_file = new_archive
        logger.info(' 移除套娃文件夹： [{}] -> [{}]'.format(last, new_path))
    return new_path if new_path else path


def insert_RJ(timeline: Timeline):
    file_name = timeline.get_current_record().output_file.name
    if not re.compile(r'[RBV]J(\d{6}|\d{8})(?!\d+)').search(file_name.upper()):
        archives = timeline.get_all_input_archives()
        archives.extend(timeline.get_all_output_archives())
        for archive in archives:
            try:
                rj = archive.RJ_code
            except AttributeError:
                rj = re.compile(r'[RBV]J(\d{6}|\d{8})(?!\d+)').search(archive.name.upper())
                rj = None if not rj else rj.group()
            if rj:
                break
        else:
            return

        old_path = timeline.get_current_path()
        new_path = old_path + '-' + rj
        os.rename(old_path, new_path)

        new_archive = Archive(new_path)
        timeline.add_record(Record(Archive(timeline.get_current_path()), 'insert_RJ', new_archive))
        logger.info(' 文件夹重命名插入RJ：  [{}] -> [{}]'.format(old_path, new_path))


# loop of unzip
# progress:
# 0.find_zip
# 0.1.pre_filter
# 0.2.unzip
# 0.3.rm_taowa
# 1.insert_RJ
# 2.post_filter
# 3.rename


def unzip_loop(progress_ui):
    for index, timeline in enumerate(timelines):
        ops = timeline.records[-1].ops
        if not ops == 'find_zip':
            continue
        zip: zip.Zip = timeline.get_current_record().output_file
        # pre filter
        newzip = copy.deepcopy(zip)
        newzip.file_list = filter.pre_filter(zip.file_list)
        timeline.add_record(Record(zip, 'pre_filter', newzip))
        # unzip
        if conf.output_path not in newzip.path:
            output_path = os.path.join(conf.output_path, newzip.filename)
        else:
            output_path = os.path.join(newzip.father, newzip.filename)
            if os.path.exists(output_path):
                output_path = os.path.join(newzip.father, "prekikoeru")
                output_path = os.path.join(output_path, newzip.filename)
                # 文件路径
        if not unzipper.unzip(newzip, output_path, conf.max_thread, progress_ui):
            continue
        output = Archive(output_path)
        timeline.add_record(Record(newzip, 'unzip', output))
        # delete_after_unzip or delete_after_reunzip
        if zip.del_after_unzip:
            for volume in zip.volumes:
                delete_file(volume)
        # rm_taowa
        new_path = rm_taowadir(timeline.get_current_path())
        new_archive = Archive(new_path)
        timeline.add_record(Record(output, 'rm_taowa', new_archive))
        # find_zip
        zip_list = []
        unzipper.find_zip(new_path, conf.passwords, conf.del_after_reunzip, already_add, zip_list)
        if len(zip_list) > 0:
            if len(zip_list) == 1:
                timeline.add_record(Record(new_archive, 'find_zip', zip_list[0]))
            else:
                done.append(timeline)
                timelines.pop(index)
                for find in zip_list:
                    t = Timeline(new_archive, 'find_zip', find)
                    timelines.append(t)
        progress_ui.add2lis(timelines)
        # loop
        if len(zip_list) > 0:
            unzip_loop(progress_ui)


def insert_rj_loop(progress_ui):
    for timeline in timelines:
        insert_RJ(timeline)
        progress_ui.add2lis(timelines)


def filter_loop(progress_ui):
    for timeline in timelines:
        input = timeline.get_current_record().output_file
        filter.post_filter(input.path)
        timeline.add_record(Record(input, 'post_filter', Archive(input.path)))

        progress_ui.add2lis(timelines)


def rename_loop(progress_ui):
    path_list = []
    # 走到这里时的路径可能是子文件夹，从子文件夹到输出路径中取出最外层文件夹
    for timeline in timelines:
        path = timeline.get_current_path()
        rel = os.path.relpath(path, conf.output_path)
        father = os.path.join(conf.output_path, rel.split('\\')[0])
        path_list.append(father)
    output_list = dlrenamer.ez_client.run_renamer(path_list)
    if output_list and len(output_list) > 0 and len(output_list) == len(timelines):
        for i in range(len(output_list)):
            timelines[i].add_record(Record(Archive(path_list[i]), 'rename', Archive(output_list[i])))
    progress_ui.add2lis(timelines)
    for t in done:
        logger.info(t)
    for t in timelines:
        logger.info(t)


def create_timeline(files, in_progress, progress_ui):
    if in_progress == 0:
        for file in files:
            zip_list = []
            if unzipper.find_zip(file, conf.passwords, conf.del_after_unzip, already_add, zip_list):
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


def timelines_runner(task_list: list, progress_ui):
    for task in task_list:
        if task == 'unzip':
            for timeline in timelines:
                record = timeline.get_current_record
                if record.ops == 'unzip':
                    unzip_loop(timeline, progress_ui)

    pass


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
