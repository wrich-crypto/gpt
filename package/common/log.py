import logging
import os
from datetime import datetime

class Logger:
    def __init__(self, name, level=logging.DEBUG, log_to_file=False):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        if log_to_file:
            today = datetime.today().strftime('%Y-%m-%d')
            log_folder = f'logs/{today}'
            if not os.path.exists(log_folder):
                os.makedirs(log_folder)
            file_name = f'{log_folder}/app.log'

            try:
                file_handler = logging.FileHandler(file_name)
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)
            except Exception as e:
                print(f'Error when setting log file: {e}')

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def debug(self, message):
        try:
            self.logger.debug(message)
        except Exception as e:
            print(f'Error when logging debug message: {e}')

    def info(self, message):
        try:
            self.logger.info(message)
        except Exception as e:
            print(f'Error when logging info message: {e}')

    def warning(self, message):
        try:
            self.logger.warning(message)
        except Exception as e:
            print(f'Error when logging warning message: {e}')

    def error(self, message):
        try:
            self.logger.error(message)
        except Exception as e:
            print(f'Error when logging error message: {e}')

    def critical(self, message):
        try:
            self.logger.critical(message)
        except Exception as e:
            print(f'Error when logging critical message: {e}')
