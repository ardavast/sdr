#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
import scipy.signal as signal
import matplotlib.pyplot as plt

import rtlsdr

sdr = rtlsdr.RtlSdr()

## configure device
sdr.sample_rate = 1.92e6
#sdr.center_freq = 97.6e6
sdr.center_freq = 104e6
sdr.gain = 30

data = sdr.read_samples(100 * 8192)
sdr.close()

data = signal.resample(data, int(len(data)/6))

data = np.angle(data[1:] * np.conj(data[:-1]))
data *= 320e3 / (2 * np.pi * 75e3)

plt.psd(data, NFFT=1024, Fs=320e3, window=signal.get_window('blackmanharris', 1024))
plt.show()
