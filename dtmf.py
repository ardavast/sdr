#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import random
import time
import numpy as np
import pyaudio

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame

key2num = {
        pygame.K_1: '1',
        pygame.K_2: '2',
        pygame.K_3: '3',
        pygame.K_4: '4',
        pygame.K_5: '5',
        pygame.K_6: '6',
        pygame.K_7: '7',
        pygame.K_8: '8',
        pygame.K_9: '9',
        pygame.K_0: '0'
}

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

    def getWave(self, amp, freq, length):
        wave = np.zeros(length)

        for i in range(length):
            wave[i] = amp * self.wavetable[self.phase]
            self.phase += freq
            if self.phase >= self.sampleRate:
                self.phase -= self.sampleRate

        return wave

sampleRate = 44100
amp = 0.2
gAudioBuffer = np.zeros(64, dtype=np.float32)
currentKeys = []
lastKeyReleased = None
phase = 0
rampCounterUp = 0
rampCounterUpEn = False
rampCounterDown = 0
rampCounterDownEn = False

hNCO = NCO(sampleRate)
vNCO = NCO(sampleRate)

def makeTone(num, length):
    f1, f2 = num2freq[num]
    return (hNCO.getWave(0.5 * amp, f1, length) +
            vNCO.getWave(0.5 * amp, f2, length))

def audio_cb(input_data, frame_count, time_info, status_flag):
    global gAudioBuffer
    global currentKeys
    global lastKeyReleased
    global rampCounterUp
    global rampCounterUpEn
    global rampCounterDown
    global rampCounterDownEn

    if rampCounterDownEn:
        if rampCounterDown - frame_count > 0:
            envelope = 1/220 * np.arange(rampCounterDown, rampCounterDown - frame_count, -1)
        else:
            envelope = 1/220 * np.arange(rampCounterDown, 0, -1)
            rampCounterDownEn = False

        if len(envelope) < len(gAudioBuffer):
           envelope = np.pad(envelope, (0, len(gAudioBuffer) - len(envelope)))

        gAudioBuffer[:] = makeTone(lastKeyReleased, frame_count)
        gAudioBuffer *= envelope

        rampCounterDown -= frame_count

    elif currentKeys:
        num = currentKeys[-1]
        gAudioBuffer[:] = makeTone(num, frame_count)

        if rampCounterUpEn:
            if rampCounterUp + frame_count < 220:
                envelope = 1/220 * np.arange(rampCounterUp, rampCounterUp + frame_count, 1)
            else:
                envelope = 1/220 * np.arange(rampCounterUp, 220, 1)
                rampCounterUpEn = False

            if len(envelope) < len(gAudioBuffer):
               envelope = np.pad(envelope, (0, len(gAudioBuffer) - len(envelope)), mode='edge')

            gAudioBuffer *= envelope
            rampCounterUp += frame_count

        return (gAudioBuffer, pyaudio.paContinue)
    else:
        gAudioBuffer[:] = np.zeros(frame_count, dtype=np.float32)

    return (gAudioBuffer, pyaudio.paContinue)

def main():
    global currentKeys
    global lastKeyReleased
    global rampCounterUp
    global rampCounterUpEn
    global rampCounterDown
    global rampCounterDownEn

    p = pyaudio.PyAudio()
    stream = p.open(output=True,
                    channels=1,
                    rate=sampleRate,
                    format=pyaudio.paFloat32,
                    frames_per_buffer=64,
                    stream_callback=audio_cb)

    pygame.init()
    screen = pygame.display.set_mode((320, 240))
    stream.start_stream()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_1, pygame.K_2, pygame.K_3,
                                 pygame.K_4, pygame.K_5, pygame.K_6,
                                 pygame.K_7, pygame.K_8, pygame.K_9,
                                 pygame.K_0]:
                    if not currentKeys:
                        rampCounterUpEn = True
                        rampCounterUp = 0
                    currentKeys.append(key2num[event.key])

            elif event.type == pygame.KEYUP:
                if event.key in [pygame.K_1, pygame.K_2, pygame.K_3,
                                 pygame.K_4, pygame.K_5, pygame.K_6,
                                 pygame.K_7, pygame.K_8, pygame.K_9,
                                 pygame.K_0]:
                    while key2num[event.key] in currentKeys:
                        currentKeys.remove(key2num[event.key])
                    lastKeyReleased = key2num[event.key]
                    if not currentKeys:
                        rampCounterDownEn = True
                        rampCounterDown = 220

            elif event.type == pygame.QUIT:
                raise SystemExit(1)

        prevKeys = currentKeys
        pygame.time.wait(10)

if __name__ == '__main__':
    main()
