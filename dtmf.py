#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import sys

import numpy as np
import sounddevice as sd
from matplotlib import pyplot as plt

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel

class Osc:
    def __init__(self, sampleRate):
        self.sampleRate = sampleRate
        self.phase = 0

    def get(self, freq, length):
        step = (2 * np.pi * freq) / self.sampleRate
        phases = self.phase + np.repeat(step, length).cumsum()
        self.phase = phases[-1] % (2 * np.pi)
        return np.sin(phases)

class OscDTMF:
    def __init__(self, sampleRate):
        self.sampleRate = sampleRate
        self.oscH = Osc(sampleRate)
        self.oscV = Osc(sampleRate)

    def get(self, num, length):
        freqH, freqV = {
            '1': (697, 1209),
            '2': (697, 1336),
            '3': (697, 1477),
            '4': (770, 1209),
            '5': (770, 1336),
            '6': (770, 1477),
            '7': (852, 1209),
            '8': (852, 1336),
            '9': (852, 1477),
            '0': (941, 1336),
        }[num]
        return 0.5 * (self.oscH.get(freqH, length) +
                      self.oscV.get(freqV, length))

class AREnvelope:
    def __init__(self, sampleRate, A, R):
        self.sampleRate = sampleRate
        self.attackSamples = round(A * sampleRate)
        self.releaseSamples = round(R * sampleRate)
        self.amp = 0
        self.state = 'off'

    def get(self, length):
        buf = []

        for i in range(length):
            if self.state == 'off':
                self.amp = 0

            if self.state == 'attack':
                if self.attackSamples and self.amp < 1:
                    self.amp += 1/self.attackSamples
                    if self.amp > 1:
                        self.amp = 1
                else:
                    self.amp = 1

            elif self.state == 'release':
                if self.releaseSamples and self.amp > 0:
                    self.amp -= 1/self.releaseSamples
                    if self.amp < 0:
                        self.amp = 0
                        self.state = 'off'
                else:
                    self.amp = 0
                    self.state = 'off'

            buf.append(self.amp)

        return np.array(buf)

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.key2num = {
            QtCore.Qt.Key_1: '1',
            QtCore.Qt.Key_2: '2',
            QtCore.Qt.Key_3: '3',
            QtCore.Qt.Key_4: '4',
            QtCore.Qt.Key_5: '5',
            QtCore.Qt.Key_6: '6',
            QtCore.Qt.Key_7: '7',
            QtCore.Qt.Key_8: '8',
            QtCore.Qt.Key_9: '9',
            QtCore.Qt.Key_0: '0',
        }

        self.currentNums = []
        self.setWindowTitle('DTMF')
        self.audio = Audio(44100, 0.5)

    def keyPressEvent(self, e):
        if not e.isAutoRepeat():
            if e.key() in self.key2num:
                num = self.key2num[e.key()]
                self.currentNums.append(num)
                self.audio.play(num)

    def keyReleaseEvent(self, e):
        if not e.isAutoRepeat():
            if e.key() in self.key2num:
                num = self.key2num[e.key()]
                while num in self.currentNums:
                    self.currentNums.remove(num)
                if self.currentNums:
                    self.audio.play(self.currentNums[-1])
                else:
                    self.audio.stop(num)

class Audio:
    def __init__(self, sampleRate, amp):
        self.sampleRate = sampleRate
        self.oscDTMF = OscDTMF(sampleRate)
        self.envelope = AREnvelope(sampleRate, 0.005, 0.005)
        self.amp = amp
        self.num = None

        sd.OutputStream(
            samplerate=self.sampleRate,
            blocksize=64,
            channels=1,
            callback=self.audioCallback).start()

    def play(self, num):
        self.num = num
        self.envelope.state = 'attack'

    def stop(self, num):
        self.num = num
        self.envelope.state = 'release'

    def audioCallback(self, outdata, frames, time, status):
        if self.envelope.state == 'off':
            buf = np.zeros(frames)
        else:
            buf = self.oscDTMF.get(self.num, frames)
            env = self.envelope.get(frames)
            buf = self.amp * buf * env

        buf = buf.reshape(-1, 1)
        outdata[:] = buf

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
