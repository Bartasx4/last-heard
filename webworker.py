import websocket
import json
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal
import logging

log = logging.getLogger(__name__)


class WebsocketWorker(QThread):
    message_received = pyqtSignal(dict)

    def __init__(self, request: str):
        super().__init__()
        self.request = request
        # For checking bad messages
        self.last_message = None

    def run(self):
        url = 'wss://api.brandmeister.network/lh/?EIO=4&transport=websocket'
        ws = websocket.WebSocketApp(url, on_message=self._on_message)
        log.debug('Run forever.')
        ws.run_forever()

    def _on_message(self, ws: websocket.WebSocketApp, received_message: str):
        message = received_message
        if self.last_message:
            log.debug('Message not serialized.', extra=self.last_message)
            self.last_message = None
        if len(message) <= 10:
            print(message)
        if message.startswith('0{"sid":'):
            ws.send('40')
            return
        if message.startswith('40{"sid":'):
            # ws.send('42["searchMongo",{"query":{"sql":"Master = 2602 OR Master = 2402"},"amount":200}]')
            ws.send(self.request)
            return
        if message == '2':
            ws.send('3')
            return
        if len(message) <= 5:
            return
        serialized = self.serialize_message(message)
        if serialized:
            self.last_message = None
            self.message_received.emit(serialized)

    @staticmethod
    def get_readable_time(start_str: str, stop_str: str):
        date_format = '%Y-%m-%d'
        time_format = '%H:%M:%S'
        date = datetime.fromtimestamp(int(start_str)).strftime(date_format)
        if len(start_str) <= 4:
            return {
                'Date_sort': date,
                'Date': date,
                'Duration': '',
                'Start': '',
            }
        start = datetime.fromtimestamp(int(start_str))
        if len(stop_str) > 4:
            stop = datetime.fromtimestamp(int(stop_str))
            duration = stop-start
            stop = stop.strftime(time_format)
        else:
            stop = ''
            duration = '0'
        full_date = start.strftime(f'{date_format} {time_format}')
        start = start.strftime(time_format)
        message = {
            'Date_sort': full_date,
            'Date': date,
            'Duration': str(duration),
            'Start-Stop': f'{start}-{stop}',
        }
        return message

    def serialize_message(self, message: str):
        data = json.loads(message[2:])
        data = data[1]
        data['payload'] = json.loads(data['payload'])
        payload = data['payload']
        payload['topic'] = data['topic']

        if not payload['SourceCall'] or not payload['DestinationID']:
            return None

        show_name = str(payload['SourceCall']).strip() if 'SourceCall' in payload else ''
        if 'SourceName' in payload and payload['SourceName']:
            show_name = f'{show_name} ({payload["SourceName"]})'

        new_message = {
            'SessionID': str(payload['SessionID']).strip(),
            'SessionType': str(payload['SessionType']).strip(),
            'SourceID': str(payload['SourceID']).strip(),
            'DestinationID': str(payload['DestinationID']).strip(),
            'SourceCall': str(payload['SourceCall']).strip(),
            'SourceName': str(payload['SourceName']).strip(),
            'TalkerAlias': str(payload['TalkerAlias']).strip(),
            'DestinationCall': str(payload['DestinationCall']).strip(),
            'DestinationName': str(payload['DestinationName']).strip(),
            'Master': str(payload['Master']).strip(),
            'FlagSet': str(payload['FlagSet']).strip(),
            'Event': str(payload['Event']).strip(),
            'Start': str(payload['Start']).strip(),
            'Stop': str(payload['Stop']).strip(),
            'State': str(payload['State']).strip(),
            'ShowName': show_name,
            # '': payload[''],
        }

        new_message.update(self.get_readable_time(new_message['Start'], new_message['Stop']))
        return new_message
