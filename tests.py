import csv
import re
import pycountry
from os import path
import logging.config
from PyQt6.QtWidgets import QApplication
from webworker import WebsocketWorker


log = logging.getLogger('tests')
log_file_name = 'logging.conf'
log_file_path = path.join(path.dirname(path.abspath(__file__)), log_file_name)

logging.config.fileConfig(log_file_path, disable_existing_loggers=True)


def _new_message(message):
    messages.append(message)
    print(message)
    # print(f'\r{len(messages)}', end='')


country_code = {}
with open('help_data/country_code.csv', 'r', encoding='UTF-8') as file:
    first_line = True
    for line in csv.reader(file):
        if first_line:
            first_line = False
            continue
        country_code[line[0]] = line[1]

with open('help_data/CallSignSeriesRanges.csv', 'r', encoding='UTF-8') as file:
    csv_data = list(csv.DictReader(file))

new_data = {}
for row in csv_data:
    series = row['Series']
    allocated = row['Allocated to'].strip()
    prefix = series[:2]
    if allocated not in new_data:
        new_data[allocated] = set()
    if re.search(f'- {prefix}\w$', series):
        new_data[allocated].add(prefix)
    else:
        new_data[allocated].add(series)

final_data = {}
not_sorted = []
for country_name, country_codes in new_data.items():
    country = pycountry.countries.get(name=country_name)
    if not country:
        country = pycountry.countries.get(official_name=country_name)
    if not country:
        not_sorted.append([country_name, country_codes])
        continue
    final_data[country.alpha_2] = country_codes

with open('help_data/country_call_prefix.txt', 'w') as file:
    for country, codes in final_data.items():
        row = ','.join(codes)
        row = f'{country}:{row}\n'
        file.write(row)

for c in not_sorted:
    print(c)
print(len(not_sorted))

print(final_data)

print('Start')
log.debug('Tests')
exit()

messages = []

request = '42["searchMongo",{"query":{"sql":"( DestinationID != 4000 ) "},"amount":200}]'
worker = WebsocketWorker(request)
worker.message_received.connect(_new_message)
worker.start()

app = QApplication([])
app.exec()
