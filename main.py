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

    logger = pk_logger.Pk_logger('task_runner', 'log.txt').add_log_handler().get_logger()

    pool = unzip_process_pool.UnzipProcessPool(conf.max_thread, 2, logger)



    task_runner.logger = logger
    task_runner.conf = conf
    task_runner.passwords = passwords
    task_runner.unzipper = unzipper.Unzipper(logger, pool)
    task_runner.filter = filter.Filter(conf.filter_kw, conf.filter_dir,logger)

    gui.init_ui()
    ui = gui.UI

    pool.shutdown()
    # print('d')
    # task_runner.progress_ui = ui