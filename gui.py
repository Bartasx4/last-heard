import json
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
        self.resize(1200, 800)
        # self.setGeometry(100, 100, 1200, 800)

        # General layout
        self.general_layout = QGridLayout()
        self.central_widget = QWidget()
        self.central_widget.setLayout(self.general_layout)
        self.setCentralWidget(self.central_widget)

        self.worker = None
        self.user_list = []

        self._load_master_file()
        self._load_country_prefix_file()
        self._load_talkgroup_file()
        self._set_predefined_talkgroup_list()

        self._create_last_heard_panel()
        self._create_browse_panel()
        self._create_search_panel()
        self._create_status_bar()

        self.general_layout.setColumnStretch(0, 2)
        self.general_layout.setColumnStretch(1, 2)
        self.general_layout.setColumnStretch(2, 1)

        self._handle_search_category_change()

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
        self.search_category = QComboBox()
        self.search_category.addItems(self.SEARCH_CATEGORY.keys())
        self.search_category.currentIndexChanged.connect(self._handle_search_category_change)
        self.search_object = QComboBox()
        self.search_object.setEditable(True)
        self.search_button = QPushButton('Śledź')
        self.search_button.clicked.connect(self._handle_search_button_clicked)
        self.search_list = QListWidget()
        search_panel_layout = QGridLayout()
        search_panel_layout.addWidget(QLabel('Kategoria'), 0, 0, alignment=Qt.AlignmentFlag.AlignRight)
        search_panel_layout.addWidget(self.search_category, 0, 1, 1, 2)
        search_panel_layout.addWidget(QLabel('Obiekt'), 1, 0, alignment=Qt.AlignmentFlag.AlignRight)
        search_panel_layout.addWidget(self.search_object, 1, 1, 1, 2)
        search_panel_layout.addWidget(self.search_button, 2, 1)
        search_panel_layout.setColumnStretch(2, 1)

        search_layout = QVBoxLayout()
        search_layout.addLayout(search_panel_layout)
        search_layout.addWidget(self.search_list)
        self.general_layout.addLayout(search_layout, 0, 2)

    def _create_status_bar(self):
        self.statusbar = self.statusBar()

    def _set_predefined_talkgroup_list(self):
        country_list = ['PL', 'SE']
        group_list = self.SEARCH_CATEGORY['Grupa']
        predefined_list = []
        new_list = []
        while group_list:
            item = group_list.pop()
            country_id = self.get_talkgroup_country(item[1])
            if self.master_by_id(country_id) in country_list:
                predefined_list.append(item)
            else:
                new_list.append(item)
        new_list = sorted(predefined_list, key=lambda item: item[1]) + new_list
        self.SEARCH_CATEGORY['Grupa'] = new_list

    def _load_master_file(self):
        with open('help_data/master.json', 'r') as file:
            data = json.load(file)
        country = [(element['country'], str(element['id'])) for element in data]
        self.SEARCH_CATEGORY['Kraj'] = sorted(country, key=lambda item: item[0])

    def _load_talkgroup_file(self):
        self.talkgroup = {}
        with open('help_data/talkgroup.json', 'r') as file:
            data = json.load(file)
        talkgroup = [(group_name, group_id) for group_id, group_name in data.items()]
        self.SEARCH_CATEGORY['Grupa'] = talkgroup

    def _load_country_prefix_file(self):
        with open('help_data/country_prefix.json', 'r') as file:
            country_prefix = json.load(file)
        self.country_prefix = {key: value.upper() for key, value in country_prefix.items()}

    def _handle_search_category_change(self):
        category = self.search_category.currentText()
        self.search_enabled = False
        self.search_object.setEditText('')
        self.search_list.clear()
        self.search_object.clear()
        self.search_hint.clear()

        for element in self.SEARCH_CATEGORY[category]:
            if category == 'Kraj':
                country = element[0]
            elif category == 'Grupa':
                country = self.master_by_id(self.get_talkgroup_country(element[1]))
            else:
                country = None
            if country:
                icon_path = f'flag/{country.lower()}.png'
                icon = QIcon(icon_path)
                item = QListWidgetItem(icon, element[0])
                self.search_object.addItem(icon, element[0])
            else:
                item = QListWidgetItem(element[0])
                self.search_object.addItem(element[0])
            self.search_hint.append(element[0])
            self.search_list.addItem(item)

        if category == 'Znak':
            self.search_list.addItems(self.user_list)

        completer = QCompleter(self.search_hint)
        self.search_object.setCompleter(completer)

    def _handle_search_button_clicked(self):
        self.search_enabled = True
        self.last_heard_table.clearContents()
        selected_category = self.search_category.currentText()
        if selected_category == 'Kraj':
            return_category = 'Master'
        elif selected_category == 'Grupa':
            return_category = 'DestinationID'
        else:
            return_category = None
        selected_object = self.search_object.currentText()
        return_object = None
        for element in self.SEARCH_CATEGORY[selected_category]:
            if selected_object == element[0]:
                return_object = element
        data = {
            'category': return_category,
            'object': return_object
        }
        self.track_enabled.emit(data)

    def get_talkgroup_country(self, talkgroup_id: str) -> str | None:
        prefix = talkgroup_id[:3]
        if prefix in self.country_prefix:
            for element in self.SEARCH_CATEGORY['Kraj']:
                if element[0] == self.country_prefix[prefix]:
                    return element[1]

    def add_message(self, table: QTableWidget, message: dict):
        new_row = [
            QTableWidgetItem(message['Date_sort'] if 'Date_sort' in message else ''),
            QTableWidgetItem(message['Date'] if 'Date' in message else ''),
            QTableWidgetItem(message['Start-Stop'] if 'Start-Stop' in message else ''),
            QTableWidgetItem(message['Duration'] if 'Duration' in message else ''),
            QTableWidgetItem(message['ShowName'] if 'ShowName' in message else ''),
            QTableWidgetItem(message['TalkerAlias'] if 'TalkerAlias' in message else ''),
            self.new_destination_item(message['DestinationID']),
            self.new_master_item(message['Master']),
        ]
        table.insertRow(0)

        for column, element in enumerate(new_row):
            table.setItem(0, column, element)

    def new_table_item(self, label: str, master_id: str | None = None) -> QTableWidgetItem:
        item = QTableWidgetItem(label)
        if master_id:
            for element in self.SEARCH_CATEGORY['Kraj']:
                if master_id == element[1]:
                    icon = QIcon(f'flag/{element[0]}.png')
                    item.setIcon(icon)
                    break
        return item

    def new_master_item(self, master_id: str):
        return self.new_table_item(self.master_by_id(master_id), master_id)

    def new_destination_item(self, destination_id: str):
        destination_name = self.destination_by_id(destination_id)
        if destination_name:
            label = destination_name + f' ({destination_id})'
        else:
            label = destination_id
        country = self.get_talkgroup_country(destination_id)
        return self.new_table_item(label, country)

    def master_by_id(self, id_):
        for element in self.SEARCH_CATEGORY['Kraj']:
            if element[1] == id_:
                return element[0]

    def destination_by_id(self, id_: str) -> str | None:
        for element in self.SEARCH_CATEGORY['Grupa']:
            if element[1] == id_:
                return element[0]
        return None

    def update_user_list(self, new_list):
        if len(new_list) != self.user_list:
            self.user_list = sorted(new_list)
            if self.search_category.currentText() == 'Znak':
                self._handle_search_category_change()
