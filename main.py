# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import multiprocessing

import config
import filter
import gui
import password
import pk_logger
import task_runner
import unzip_process_pool
import unzipper

if __name__ == '__main__':
    multiprocessing.freeze_support()
    conf = config.Config()
    gui.output = conf.output_path

    passwords = password.read_password()

    # progress = pk_logger.Pk_logger('progress').add_progress_handler().get_logger()
    logger = pk_logger.Pk_logger('task_runner', 'log.txt').add_log_handler().get_logger()

    resource = unzip_process_pool.ProcessResourceManager(2)

    task_runner.logger = logger
    task_runner.conf = conf
    task_runner.passwords = passwords
    task_runner.unzipper = unzipper.Unzipper(logger, resource)
    task_runner.filter = filter.Filter(conf.filter_kw, conf.filter_dir, logger)

    gui.init_ui(resource.log_queue)

    pool = unzip_process_pool.ProcessPool(conf.max_thread, resource)

    gui.mainloop_ui()
    # ui = gui.UI

    resource.log_queue.put(None)

    pool.shutdown()
    # print('d')
    # task_runner.progress_ui = ui
