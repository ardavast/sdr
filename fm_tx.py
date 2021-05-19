#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Offline FM transmiiter
# Expects a 32k 16-bit mono .wav file as input
#
# Example usage:
# ffmpeg -i song.mp3 -ac 1 -ar 32000 song.wav
# python3 fm_tx.py song.wav song.raw
# hackrf_transfer -f 100e6 -s 8e6 -x 20 -t song.raw

# CAUTION: A 30 second (~2.5MB) .wav file will produce a ~450MB .raw file.
# Use the ffmpeg -ss and -t options to cut a part of the file.

import math
import sys
from pathlib import Path

import numpy as np
import scipy.signal as signal
import scipy.io.wavfile as wavfile
import matplotlib.pyplot as plt

RF_RATE = 8000000
IF_RATE = RF_RATE / 25
AUDIO_RATE = IF_RATE / 10
MAX_DEV = 75e3

def complexToInterleaved(x):
    y = np.empty(x.size * 2, dtype=np.float32)
    y[0::2] = x.real
    y[1::2] = x.imag
    return y

if len(sys.argv) < 3:
    exit(f'Usage: {__file__} {{uint8|complex64}} <WAV file> <RF file>')

wavFile = Path(sys.argv[1])
rfFile = Path(sys.argv[2])

# Load the entire WAV file into memory
data = wavFile.read_bytes()

# Remove the WAV header if present
if data[0:4] == b'RIFF':
    hdrLen = data.find(b'data')
    if hdrLen == -1:
        sys.exit("Can't find the data section in the WAV header")
    else:
        hdrLen += 8
    data = data[hdrLen:]

# After this block the data will consist of float32 samples
data = np.frombuffer(data, dtype=np.int16)
data = data.astype(np.float32)
data = (data + 0.5) / 32767.5

# Interpolate to 320k
data = signal.resample(data, len(data) * 10)

# FM preemphasis filter
# TODO

# FM modulation
data = np.exp(1j*(2*np.pi * np.cumsum(data * MAX_DEV/IF_RATE)))

# Interpolate to 8M
data = signal.resample(data, len(data) * 25)

# Write the output as a 8M 8-bit IQ file
data = complexToInterleaved(data)
data = data * 127.5 - 0.5
data = data.astype(np.int8)
rfFile.write_bytes(data)
