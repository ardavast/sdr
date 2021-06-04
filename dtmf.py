#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import random
import sys
import time

import numpy as np
import sounddevice as sd

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel

num2freq = {
    '1': (697, 1209),
    '2': (697, 1336),
    '3': (697, 1477),
    '4': (770, 1209),
    '5': (770, 1336),
    '6': (770, 1477),
    '7': (852, 1209),
    '8': (852, 1336),
    '9': (852, 1477),
    '0': (941, 1336)
}

class NCO:
    def __init__(self, sampleRate):
        self.sampleRate = sampleRate
        self.phase = 0
        self.wavetable = np.sin(2*np.pi/sampleRate * np.arange(sampleRate))

    def getWave(self, freq, length):
        step = (2 * np.pi * freq) / self.sampleRate
        phases = self.phase + np.repeat(step, length).cumsum()
        self.phase = phases[-1] % (2 * np.pi)
        return np.sin(phases)

sampleRate = 44100
amp = 0.2
currentKeys = []
lastKeyReleased = None
rampCounterUp = 0
rampCounterUpEn = False
rampCounterDown = 0
rampCounterDownEn = False

hNCO = NCO(sampleRate)
vNCO = NCO(sampleRate)

def makeTone(num, length):
    f1, f2 = num2freq[num]
    return amp * (0.5 * hNCO.getWave(f1, length) +
                  0.5 * vNCO.getWave(f2, length))

def audioCallback(outdata, frames, time, status):
    global currentKeys
    global lastKeyReleased
    global rampCounterUp
    global rampCounterUpEn
    global rampCounterDown
    global rampCounterDownEn

    if rampCounterDownEn:
        if rampCounterDown - frames > 0:
            envelope = 1/220 * np.arange(rampCounterDown, rampCounterDown - frames, -1)
        else:
            envelope = 1/220 * np.arange(rampCounterDown, 0, -1)
            rampCounterDownEn = False

        if len(envelope) < len(outdata):
           envelope = np.pad(envelope, (0, len(outdata) - len(envelope)))

        buf = makeTone(lastKeyReleased, frames) * envelope

        rampCounterDown -= frames

    elif currentKeys:
        num = currentKeys[-1]
        buf = makeTone(num, frames)

        if rampCounterUpEn:
            if rampCounterUp + frames < 220:
                envelope = 1/220 * np.arange(rampCounterUp, rampCounterUp + frames, 1)
            else:
                envelope = 1/220 * np.arange(rampCounterUp, 220, 1)
                rampCounterUpEn = False

            if len(envelope) < len(buf):
               envelope = np.pad(envelope, (0, len(buf) - len(envelope)), mode='edge')

            buf *= envelope
            rampCounterUp += frames
    else:
        buf = np.zeros(frames, dtype=np.float32).reshape(-1, 1)

    buf = buf.reshape(-1, 1)
    outdata[:] = buf

class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        sd.OutputStream(
            samplerate=44100,
            blocksize=64,
            channels=1,
            callback=audioCallback).start()

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

        self.setWindowTitle('DTMF')

    def keyPressEvent(self, e):
        global currentKeys
        global rampCounterUp
        global rampCounterUpEn

        key = e.key()
        if key in self.key2num:
            if not e.isAutoRepeat():
                if not currentKeys:
                    rampCounterUpEn = True
                    rampCounterUp = 0
                currentKeys.append(self.key2num[key])

    def keyReleaseEvent(self, e):
        global currentKeys
        global lastKeyReleased
        global rampCounterDown
        global rampCounterDownEn

        key = e.key()
        if key in self.key2num:
            if not e.isAutoRepeat():
                while self.key2num[key] in currentKeys:
                    currentKeys.remove(self.key2num[key])
                lastKeyReleased = self.key2num[key]
                if not currentKeys:
                    rampCounterDownEn = True
                    rampCounterDown = 220

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
