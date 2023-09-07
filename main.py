__title__ = 'Last Heard'
__author__ = 'Bartosz Szymanski'
__license__ = 'MIT'
__copyright__ = 'Copyright 2023 Bartosz Szymanski'
__version__ = '0.0.4'

import logging
import logging.config
from os import path

import sys
from PyQt6.QtWidgets import QApplication

from gui import Gui
from engine import Engine


log_file_name = 'logging.conf'
log_file_path = path.join(path.dirname(path.abspath(__file__)), log_file_name)
logging.config.fileConfig(log_file_path, disable_existing_loggers=True)


def main():
    app = QApplication([])
    gui = Gui()
    engine = Engine(gui)
    gui.show()

    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
