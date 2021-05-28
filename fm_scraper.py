#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Scrapes the FM stations in Sofia from predavatel.com and writes them to
# stations.json

import re
import json

import requests
from bs4 import BeautifulSoup

r = requests.get('http://www.predavatel.com/bg/1/sofia')
r.encoding = 'utf-8'
soup = BeautifulSoup(r.text, 'html.parser')

stations = []
for row in soup.find_all('tr', {'class': ['rt0', 'rt1']}):
    if row['class'][0] == 'rt0':
        dx = False
        cFreq, cName, cInfo = 'freq', 'fsta', 'fpre'
    elif row['class'][0] == 'rt1':
        dx = True
        cFreq, cName, cInfo = 'dxfreq', 'dxfsta', 'dxfpre'
    else:
        continue

    # Extract frequency
    freq = row.findChildren('td', {'class': cFreq})[0].text.strip()
    try:
        freq = float(freq)
        if not 87.5 <= freq <= 108.0:
            continue
    except ValueError:
        continue

    # Extract name
    name = row.findChildren('td', {'class': cName})[0].text.strip()

    # Extract location and power
    info = row.findChildren('td', {'class': cInfo})[0].text.split(',')
    location = ''.join(info[:-2]).strip()
    if not location:
        location = None

    power = info[-2].strip()
    if not re.match('^\d+\s+k?W$', power):
        power = None

    stations.append({'frequency': freq,
                     'name': name,
                     'location': location,
                     'power': power,
                     'dx': dx})

with open('stations.json', 'w') as f:
    json.dump(stations, f, ensure_ascii=False, indent=4)
