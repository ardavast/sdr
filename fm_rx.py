#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Offline FM receiver
# Works with files created from SDR#, GQRX, GNU radio file sink, rtl_sdr, etc.
# Expects that the sample rate is 1920000
#
# Example usage:
# timeout 10 rtl_sdr -f 104e6 -s 1920000 jazzfm.raw
# python3 fm_rx.py complex64 jazzfm.raw jazzfm.wav
# mplayer jazzfm.wav

# Format tips:
# For GQRX and GNU Radio complex file sink use complex64.
# For rtl_sdr use uint8.
# For SDR# make the recording with "8 Bit PCM" and "Baseband" and use uint8.
#
# CAUTION: with the wrong parameters "RIP Headphone Users" situations are
# possible, so be careful with the audio levels.

import math
import sys
from pathlib import Path

import numpy as np
import scipy.signal as signal
import scipy.io.wavfile as wavfile
import matplotlib.pyplot as plt

RF_RATE = 1920000
IF_RATE = RF_RATE / 10
AUDIO_RATE = IF_RATE / 6
MAX_DEV = 75e3

def error(msg):
    print(msg, file=sys.stderr)
    raise SystemExit(1)

if len(sys.argv) < 3:
    error(f'Usage: {__file__} {{uint8|complex64}} <RF file> <WAV file>')

rfFmt = sys.argv[1]
if rfFmt not in ['uint8', 'complex64']:
    error(f'Usage: {__file__} {{uint8|complex64}} <RF file> <WAV file>')

rfFile = Path(sys.argv[2])
wavFile = Path(sys.argv[3])

# Load the entire file into memory
data = rfFile.read_bytes()

# Remove the WAV header if present
if rfFile.name.endswith('.wav') and data[0:4] == b'RIFF':
    hdrLen = data.find(b'data')
    if hdrLen == -1:
        error("Can't find the data section in the WAV header")
    else:
        hdrLen += 8
    print(f'skip {hdrLen}')
    data = data[hdrLen:]

# After this block the data will consist of complex64 IQ samples
if rfFmt == 'uint8':
    data = np.frombuffer(data, dtype=np.uint8)
    data = data.astype(np.float32)
    data = (data - 127.5) / 127.5
    data = data.view(np.complex64)
else:
    data = np.frombuffer(data, dtype=np.complex64)

# Decimate to 192k
data = signal.decimate(data, 10, ftype='fir')

# Demodulate the FM signal
# In the simplest possible terms: This returns the difference between the phase
# of each complex sample and the phase of the previous sample
# A very good explanation of the expression below can be found at:
# https://dsp.stackexchange.com/a/2613/31366
data = np.angle(data[1:] * np.conj(data[:-1]))
data *= IF_RATE / (2 * np.pi * MAX_DEV)

# FM deemphasis filter, the coefficients are taken from: https://git.io/Js49p
# tau = 75e-6
btaps = [0.03357008637245808, 0.03357008637245808]
ataps = [1.0, -0.9328598272550838]
data = signal.lfilter(btaps, ataps, data)

# Decimate to 32k
data = signal.decimate(data, 6, ftype='fir')

# Write the output as a 32k 16-bit WAV file
data = data * 32767.5 - 0.5
data = data.astype(np.int16)
wavfile.write(wavFile, int(AUDIO_RATE), data)
