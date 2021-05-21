#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Offline FM transmiiter
# Expects a mono, 32kHz, 16-bit signed WAV file as input
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

if len(sys.argv) < 4:
    exit(f'Usage: {__file__} {{uint8|complex64}} <WAV file> <Baseband file> <RF file>')

wavFile = Path(sys.argv[1])
basebandFile = Path(sys.argv[2])
rfFile = Path(sys.argv[3])

# Load the entire WAV file into memory
wavRate, wavData = wavfile.read(wavFile)
if not (wavData.shape[1] == 2 and
        wavRate == 32000 and
        wavData.dtype == np.int16):
    sys.exit('Input format must be: stereo, 32kHz, 16-bit signed')

length = wavData.shape[0]
left = wavData[:,0]
right = wavData[:,1]

# Convert the input data to normalized floats
left = left.astype(np.float)
left = (left + 0.5) / 32767.5

right = right.astype(np.float)
right = (right + 0.5) / 32767.5

# Interpolate to 320k
length *= 10
left = signal.resample(left, length)
right = signal.resample(right, length)

# FM preemphasis filter, the coefficients are taken from: https://git.io/Js49p
# tau = 50e-6
#btaps = [29.498236311937575, -27.70989987735248]
#ataps = [1.0, 0.7883364345850924]
# tau = 75e-6
btaps = [43.80803296614535, -42.01969653156026]
ataps = [1.0, 0.7883364345850924]
left = signal.lfilter(btaps, ataps, left)
right = signal.lfilter(btaps, ataps, right)

lpr = left + right
lmr = left - right

pilot = np.cos(2 * np.pi * 19e3 / IF_RATE * np.arange(length))
lmr = lmr*np.cos(2 * np.pi * 38e3 / IF_RATE * np.arange(length))

data = 0.45*lpr + 0.1*pilot + 0.45*lmr
data /= 2

# FM modulation
data = np.exp(1j*(2*np.pi * np.cumsum(data * MAX_DEV/IF_RATE)))

# write baseband file
basebandFile.write_bytes(data.astype(np.complex64))

# Interpolate to 8M
length *= 25
data = signal.resample(data, length)

# Write the output as a 8M 8-bit IQ file
data = complexToInterleaved(data)
data = data * 127.5 - 0.5
data = data.astype(np.int8)
rfFile.write_bytes(data)
