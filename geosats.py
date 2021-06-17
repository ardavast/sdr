#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import timedelta
from operator import itemgetter

from tabulate import tabulate

from skyfield import units
from skyfield.api import E, N, load, wgs84

# Values taken from Stellarium
sofiaLat = N * units.Angle(degrees=(42, 41, 51.04)).degrees
sofiaLon = E * units.Angle(degrees=(23, 19, 26.94)).degrees
sofiaElevation = 562
sofia = wgs84.latlon(sofiaLat, sofiaLon, sofiaElevation)


def isGeostationary(sat):
    """Return True if the satellite moves by less than 1 deg in 48 hours."""
    minAlt = minAz = float('inf')
    maxAlt = maxAz = -float('inf')

    epochDt = sat.epoch.utc_datetime()
    startDt = epochDt - timedelta(hours=24)
    endDt = epochDt + timedelta(hours=24)

    dt = startDt
    while dt <= endDt:
        t = ts.from_datetime(dt)
        alt, az, _ = (sat - sofia).at(t).altaz()
        alt = alt.degrees
        az = az.degrees
        if alt < minAlt:
            minAlt = alt
        if alt > maxAlt:
            maxAlt = alt
        if az < minAz:
            minAz = az
        if az > maxAz:
            maxAz = az
        dt += timedelta(hours=1)
    return maxAlt - minAlt < 1 and maxAz - minAz < 1


ts = load.timescale()
satellites = load.tle_file('https://www.celestrak.com/NORAD/elements/geo.txt')

satPos = []
for sat in filter(isGeostationary, satellites):
    alt, az, d = (sat - sofia).at(sat.epoch).altaz()

    alt = alt.degrees
    az = az.degrees
    d = d.km

    if alt > 0:
        satPos.append((sat.name, alt, az, d))

print(tabulate(sorted(satPos, key=itemgetter(2)),
               headers=('Name', 'Alt', 'Az', 'Distance'),
               tablefmt='simple',
               floatfmt=".5f"))
