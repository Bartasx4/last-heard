import logging
from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QListWidget,
    QWidget,
    QMainWindow,
    QTableWidget,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QCompleter,
    QPushButton,
    QGridLayout,
    QListWidgetItem,
    QTableWidgetItem,
)

from content_creator import ContentCreator

log = logging.getLogger(__name__)


class Gui(QMainWindow):
    SEARCH_CATEGORY = {'Kraj': [], 'Grupa': [], 'Znak': []}
    TABLE_HEADER = {
        'Date_sort': '',
        'Date': 'Data',
        'Start-Stop': 'Godzina',
        'Duration': 'Czas',
        'DestinationID': 'Grupa',
        'ShowName': 'Użytkownik',
        'TalkerAlias': 'Alias',
        # 'Master': 'Kraj',
    }
    track_enabled = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

        self.setWindowTitle('Last Heard')
        self.resize(1200, 700)
        # self.setGeometry(100, 100, 1200, 800)

        # General layout
        self.general_layout = QGridLayout()
        self.central_widget = QWidget()
        self.central_widget.setLayout(self.general_layout)
        self.setCentralWidget(self.central_widget)

        self.worker = None
        self.callsign_list = []
        self.cc = ContentCreator()

        self._create_last_heard_panel()
        self._create_browse_panel()
        self._create_search_panel()
        self._create_status_bar()

        self.general_layout.setColumnStretch(0, 2)
        self.general_layout.setColumnStretch(1, 2)
        self.general_layout.setColumnStretch(2, 1)

        self._handle_track_category_change()

    def _create_last_heard_panel(self):
        self.last_heard_label = QLabel('Last Heard')
        self.last_heard_table = QTableWidget(0, len(self.TABLE_HEADER))
        self.last_heard_table.setHorizontalHeaderLabels(self.TABLE_HEADER.values())
        self.last_heard_table.hideColumn(0)
        self.last_heard_table.hideColumn(1)
        self.last_heard_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        last_heard_layout = QVBoxLayout()
        last_heard_layout.addWidget(self.last_heard_label)
        last_heard_layout.addWidget(self.last_heard_table)
        self.general_layout.addLayout(last_heard_layout, 0, 0)

    def _create_browse_panel(self):
        self.browse_label = QLabel('Przeglądaj')
        self.browse_table = QTableWidget(0, len(self.TABLE_HEADER))
        self.browse_table.setHorizontalHeaderLabels(self.TABLE_HEADER.values())
        self.browse_table.hideColumn(0)
        self.browse_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        browse_layout = QVBoxLayout()
        browse_layout.addWidget(self.browse_label)
        browse_layout.addWidget(self.browse_table)
        self.general_layout.addLayout(browse_layout, 0, 1)

    def _create_search_panel(self):
        self.search_hint = []
        self.search_users = []
        self.track_category = QComboBox()
        self.track_category.addItems(self.SEARCH_CATEGORY.keys())
        self.track_category.currentIndexChanged.connect(self._handle_track_category_change)
        self.track_object = QComboBox()
        self.track_object.setEditable(True)
        self.search_button = QPushButton('Śledź')
        self.search_button.clicked.connect(self._handle_search_button_clicked)
        self.search_list = QListWidget()
        search_panel_layout = QGridLayout()
        search_panel_layout.addWidget(QLabel('Kategoria'), 0, 0, alignment=Qt.AlignmentFlag.AlignRight)
        search_panel_layout.addWidget(self.track_category, 0, 1, 1, 2)
        search_panel_layout.addWidget(QLabel('Obiekt'), 1, 0, alignment=Qt.AlignmentFlag.AlignRight)
        search_panel_layout.addWidget(self.track_object, 1, 1, 1, 2)
        search_panel_layout.addWidget(self.search_button, 2, 1)
        search_panel_layout.setColumnStretch(2, 1)

        search_layout = QVBoxLayout()
        search_layout.addLayout(search_panel_layout)
        search_layout.addWidget(self.search_list)
        self.general_layout.addLayout(search_layout, 0, 2)

    def _create_status_bar(self):
        self.statusbar = self.statusBar()

    def _handle_track_category_change(self):
        category = self.track_category.currentText()
        self.track_object.setEditText('')
        self.search_list.clear()
        self.track_object.clear()
        self.search_hint.clear()

        if category == 'Kraj':
            items = [(country, country) for country in self.cc.master.keys()]
        elif category == 'Grupa':
            items = [(group[0], self.cc.get_talkgroup_country(group[1])) for group in self.cc.talkgroup]
        elif category == 'Znak':
            items = [(callsign[1], self.cc.get_callsign_country(callsign[1])) for callsign in self.callsign_list]
        else:
            return

        for item in items:
            if item[1]:
                icon_path = f'flag/{item[1].lower()}.png'
                icon = QIcon(icon_path)
                self.track_object.addItem(icon, item[0])
                widget_item = QListWidgetItem(icon, item[0])
            else:
                self.track_object.addItem(item[0])
                widget_item = QListWidgetItem(item[0])
            self.search_list.addItem(widget_item)
            self.search_hint.append(item[0])

        completer = QCompleter(self.search_hint)
        self.track_object.setCompleter(completer)

    def _handle_search_button_clicked(self):
        self.track_enabled = True
        self.last_heard_table.clearContents()
        selected_category = self.track_category.currentText()
        if selected_category == 'Kraj':
            return_category = 'Master'
        elif selected_category == 'Grupa':
            return_category = 'DestinationID'
        else:
            return_category = None
        selected_object = self.track_object.currentText()
        return_object = None
        for element in self.SEARCH_CATEGORY[selected_category]:
            if selected_object == element[0]:
                return_object = element
        data = {
            'category': return_category,
            'object': return_object
        }
        self.track_enabled.emit(data)

    def add_message(self, table: QTableWidget, message: dict):
        new_row = [
            QTableWidgetItem(message['Date_sort'] if 'Date_sort' in message else ''),
            QTableWidgetItem(message['Date'] if 'Date' in message else ''),
            QTableWidgetItem(message['Start-Stop'] if 'Start-Stop' in message else ''),
            QTableWidgetItem(message['Duration'] if 'Duration' in message else ''),
            self.cc.talk_group_item(message['DestinationID']),
            QTableWidgetItem(message['ShowName'] if 'ShowName' in message else ''),
            QTableWidgetItem(message['TalkerAlias'] if 'TalkerAlias' in message else ''),
            self.cc.master_item(message['Master']),
        ]
        table.insertRow(0)

        for column, element in enumerate(new_row):
            table.setItem(0, column, element)

    def update_user_list(self, new_list):
        if len(new_list) != self.callsign_list:
            self.callsign_list = sorted(new_list)
            if self.track_category.currentText() == 'Znak':
                self._handle_track_category_change()
