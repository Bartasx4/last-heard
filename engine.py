import logging
from PyQt6.QtWidgets import QTableWidget

from gui import Gui
from webworker import WebsocketWorker

log = logging.getLogger(__name__)


class Engine:

    request = '42["searchMongo",{"query":{"sql":"( DestinationID != 4000 ) "},"amount":200}]'

    def __init__(self, gui: Gui):
        self.gui = gui
        self.user_list = []

        self.track_filter = {'category': None, 'object': (None, None),
                             'last_group': {'category': None, 'object': (None, None)}}
        self.browse_filter = {'category': None, 'object': (None, None)}

        self.gui.track_enabled.connect(self._handle_track_start)

        self.gui.worker = WebsocketWorker(self.request)
        self.gui.worker.message_received.connect(self._handle_new_message)
        self.gui.worker.start()

        self.data = []

    def _handle_new_message(self, message: dict[str: str]):
        self.data.append(message)
        self.check_new_callsign(message)
        self.filter_and_add_message(self.gui.last_heard_table, self.track_filter, message)

    def _handle_track_start(self, track_filter: dict):
        self.track_filter.update(track_filter)
        self.update_status()
        self.change_table_content(self.gui.last_heard_table, track_filter)

    def change_table_content(self, table: QTableWidget, content_filter: dict):
        table.clearContents()
        table.setRowCount(0)
        table.setSortingEnabled(False)

        for message in self.data:
            if self.filter_message(message, content_filter):
                self.gui.add_message(table, message)

        table.resizeColumnsToContents()
        table.setSortingEnabled(False)
        table.sortItems(0)

    def check_new_callsign(self, message: dict):
        new_callsign = message['SourceCall']
        for callsign in self.user_list:
            if new_callsign == callsign[1]:
                return
        self.user_list.append((message['ShowName'], new_callsign))
        self.gui.update_user_list(self.user_list)

    def update_status(self):
        status = f'{self.track_filter["category"]}: {self.track_filter["object"]} '
        status += f'last_group: {self.track_filter["last_group"]["object"]}'
        self.gui.statusbar.showMessage(status, 3000)

    def filter_and_add_message(self, table: QTableWidget, content_filter: dict, message: dict):
        if self.filter_message(message, content_filter):
            self.gui.add_message(table, message)

    def change_last_heard_group(self, group: str):
        self.track_filter['last_group']['DestinationID'] = group
        self.change_table_content(self.gui.last_heard_table, self.track_filter['last_group'])

    @staticmethod
    def filter_message(message: dict, content_filter: dict) -> bool:
        req = [
            'category' in content_filter and
            'object' in content_filter and
            content_filter['category'] and
            content_filter['object']
        ]
        if not all(req):
            return False
        message_object = message[content_filter['category']]
        filter_object = content_filter['object'][1]
        if message_object == filter_object and message_object and filter_object:
            return True
        return False
