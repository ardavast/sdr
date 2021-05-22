#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import numpy as np
import scipy as sp
import scipy.signal as signal
import matplotlib.pyplot as plt

import rtlsdr

#plt.psd(data, NFFT=1024, Fs=44100, window=signal.get_window('boxcar', 1024))

#sdr = rtlsdr.RtlSdr()
#
## configure device
#sdr.sample_rate = 1.92e6
#sdr.center_freq = 97.6e6
#sdr.gain = 30

#data = sdr.read_samples(100 * 8192)
#sdr.close()

#data = signal.resample(data, int(len(data)/10))
#
#data = np.angle(data[1:] * np.conj(data[:-1]))
#data *= IF_RATE / (2 * np.pi * MAX_DEV)


signal1 = 1*np.cos(2*np.pi*440/44100 * np.arange(0, 44100))
signal2 = 1*np.sin(2*np.pi*8800/44100 * np.arange(0, 44100))
x = signal1 + signal2
x = x[0:4096]
X = np.fft.rfft(x)
freq = np.fft.rfftfreq(len(x), d=1/44100)
plt.plot(freq, (np.abs(X)/4096))
plt.show()
