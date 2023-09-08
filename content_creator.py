import json
import logging
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QTableWidgetItem

log = logging.getLogger(__name__)


class ContentCreator:

    def __init__(self):
        """
        master = {
            master_alpha2: {
                id: str,
                group_prefix: list[str],
                callsign_prefix: list[str],
            }
        }
        """
        self._load_master_file()
        self._load_master_group_prefix_file()
        self._load_country_call_prefix_file()
        self._load_talkgroup_file()
        self._set_predefined_talkgroup_list()

    def _set_predefined_talkgroup_list(self):
        country_list = ['PL', 'SE']
        country_temp_list = {country: [] for country in country_list}
        other_list = []
        for talkgroup in self.talkgroup:
            country = self.get_talkgroup_country(talkgroup[1])
            if country in country_list:
                country_temp_list[country].append(talkgroup)
            else:
                other_list.append(talkgroup)
        predefined_list = []
        for country in country_list:
            predefined_list += sorted(country_temp_list[country], key=lambda item: int(item[1]))
        self.talkgroup = predefined_list + other_list

    def get_talkgroup_country(self, talkgroup_id: str) -> str | None:
        if len(talkgroup_id) < 3:
            return None
        prefix = talkgroup_id[:3]
        for master, data in self.master.items():
            if prefix in data['group_prefix']:
                return master

    def get_callsign_country(self, callsign: str) -> str | None:
        if len(callsign) <= 3:
            log.error(f'Wrong callsign {callsign}.')
            return None
        prefix = callsign[:2]
        for country, data in self.master.items():
            if prefix in data['callsign_prefix']:
                return country

    def master_id_to_name(self, master_id: str) -> str | None:
        for master in self.master:
            if self.master[master]['id'] == master_id:
                return master
        log.warning(f'Not found {master_id} in master list.', extra=self.master)

    def table_item(
            self,
            label: str,
            master_id: str | None = None,
            master_name: str | None = None,
            icon: QIcon | None = None
    ) -> QTableWidgetItem:
        item = QTableWidgetItem(label)
        if master_id:
            master_name = self.master_id_to_name(master_id)
        if master_name:
            icon_path = f'flag/{master_name}.png'
            icon = QIcon(icon_path)
        if icon:
            item.setIcon(icon)
        return item

    def master_item(self, master_id: str) -> QTableWidgetItem:
        return self.table_item(self.master_id_to_name(master_id), master_id=master_id)

    def talk_group_item(self, group_id: str) -> QTableWidgetItem:
        group_name = self.talkgroup_id_to_name(group_id)
        if group_name:
            label = f'{group_name} ({group_id})'
        else:
            label = group_id
        country = self.get_talkgroup_country(group_id)
        return self.table_item(label, master_name=country)

    def talkgroup_id_to_name(self, talkgroup_id: str) -> str | None:
        for talkgroup in self.talkgroup:
            if talkgroup[1] == talkgroup_id:
                return talkgroup[0]
        log.info(f'Not found {talkgroup_id} in talkgroup list.')

    def _load_master_file(self):
        with open('help_data/master.json', 'r') as file:
            data = json.load(file)

        self.master = {}
        for element in data:
            self.master[element['country']] = {'id': str(element['id']), 'group_prefix': [], 'callsign_prefix': []}

    def _load_master_group_prefix_file(self):
        with open('help_data/country_group_prefix.json', 'r') as file:
            data = json.load(file)
        for group_prefix, master in data.items():
            master = master.upper()
            if master in self.master:
                self.master[master]['group_prefix'].append(group_prefix)
        print('ok')

    def _load_country_call_prefix_file(self):
        with open('help_data/country_call_prefix.txt', 'r') as file:
            for row in file:
                separator = row.find(':')
                master = row[:separator]
                prefix = row[separator+1:].replace('\n', '').split(',')
                if master in self.master:
                    self.master[master]['callsign_prefix'] = prefix

    def _load_talkgroup_file(self):
        self.talkgroup = []
        with open('help_data/talkgroup.json', 'r') as file:
            data = json.load(file)
        talkgroup = []
        for group_id, group_name in data.items():
            show_name = f'{group_name} ({group_id})'
            talkgroup.append((show_name, group_id))
        self.talkgroup = talkgroup
