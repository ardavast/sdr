#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Offline FM receiver
# Works with files created from SDR#, GQRX, GNU radio file sink, rtl_sdr, etc.
# Expects that the sample rate is 1920000
#
# Example usage:
# timeout 10 rtl_sdr -f 104e6 -s 1920000 jazzfm.raw
# python3 fm_rx.py uint8 jazzfm.raw jazzfm.wav
# mplayer jazzfm.wav

# Format tips:
# For GQRX and GNU Radio complex file sink use complex64.
# For rtl_sdr use uint8.
# For SDR# make the recording with "8 Bit PCM" and "Baseband" and use uint8.
#
# CAUTION: with the wrong parameters "RIP Headphone Users" situations are
# possible, so be careful with the audio levels.

import argparse
import sys

import numpy as np
import scipy.signal as signal
import utils

RF_RATE = 1920000
IF_RATE = RF_RATE / 10
AUDIO_RATE = IF_RATE / 6
MAX_DEV = 75e3

parser = argparse.ArgumentParser(description='Offline FM receiver')
parser.add_argument('inputFile', type=str,
    help='Path to a I/Q file in raw or WAV format.  Sample rate must be '
         '1.92 MHz.  With raw files the --dtype option is required.')
parser.add_argument('outputFile', type=str,
    help='Output path (WAV mono 32 kHz 16 bit signed')
parser.add_argument('--dtype', type=str,
                    choices=['uint8', 'int8', 'int16', 'float32', 'complex64'])
args = parser.parse_args()

# Load the entire file into memory
try:
    _, data = utils.readFile(args.inputFile, args.dtype, IQfile=True)
except Exception as e:
    sys.exit(e)

if data.dtype != np.complex:
    sys.exit(f'{args.inputFile} is not an I/Q file')

# Decimate to 192k
data = signal.decimate(data, 10, ftype='fir')

# Demodulate the FM signal
# In the simplest possible terms: This takes the difference between the phase
# of each complex sample and the phase of the previous sample, and then scales
# that phase difference to get the correct amplitude of the message signal.
# A very good explanation of the expression below can be found at
# https://dsp.stackexchange.com/a/2613/31366
data = np.angle(data[1:] * np.conj(data[:-1]))
data *= IF_RATE / (2 * np.pi * MAX_DEV)

# FM deemphasis filter, the coefficients are taken from: https://git.io/Js49p
# tau = 50e-6
# btaps = [0.005181393759023543, 0.005181393759023543]
# ataps = [1.0, -0.989637212481953]
# tau = 75e-6
btaps = [0.03357008637245808, 0.03357008637245808]
ataps = [1.0, -0.9328598272550838]
data = signal.lfilter(btaps, ataps, data)

# Decimate to 32k
data = signal.decimate(data, 6, ftype='fir')

# Write the output as a 32k 16-bit WAV file
utils.writeFile(data, args.outputFile, np.int16, int(AUDIO_RATE), wavFile=True)
