#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np
import scipy.io.wavfile as wavfile

validDTypes = (np.uint8, np.int8, np.int16, np.float32, np.complex64)

def interleaveComplex(c):
    if c.dtype != np.complex:
        raise TypeError("Argument must be complex")
    f = np.empty(c.size * 2, dtype=np.float)
    f[0::2] = c.real
    f[1::2] = c.imag
    return f

def toFloat(data):
    if data.dtype == np.uint8:
        return (data.astype(np.float) - 127.5) / 127.5
    elif data.dtype == np.int8:
        return (data.astype(np.float) + 0.5) / 127.5
    elif data.dtype == np.int16:
        return (data.astype(np.float) + 0.5) / 32767.5
    elif data.dtype == np.float32:
        return data.astype(dtype)
    else:
        raise ValueError(f"Unsupported dtype: {data.dtype}")

def fromFloat(data, dtype):
    if data.dtype != np.float:
        raise TypeError("Argument must be float")
    dtype = np.dtype(dtype)
    if dtype == np.uint8:
        return (data * 127.5 + 127.5).astype(dtype)
    elif dtype == np.int8:
        return (data * 127.5 - 0.5).astype(dtype)
    elif dtype == np.int16:
        return (data * 32767.5 - 0.5).astype(dtype)
    elif dtype == np.float32:
        return data.astype(dtype)
    else:
        raise ValueError(f"Unsupported dtype: {dtype}")

def readFile(filename, dtype=None, IQfile=False):
    try:
        rate, data = wavfile.read(filename)
        wavFile = True
    except Exception:
        wavFile = False

    if wavFile:
        if data.dtype not in validDTypes:
            raise ValueError(f"Unsupported dtype: {data.dtype}")

        if (not 0 < len(data.shape) <= 2 or
            len(data.shape) == 2 and data.shape[1] not in [1, 2]):
            raise ValueError(f'Invalid shape: {data.shape}')

        data = toFloat(data)
        if len(data.shape) > 1 and data.shape[1] == 2:
            if IQFormat:
                data = data[:,0] + 1j * data[:,1]
    else:
        rate = None

        if not dtype:
            raise ValueError("dtype must be set for raw files")
        dtype = np.dtype(dtype)
        if dtype not in validDTypes:
            raise ValueError(f"Unsupported dtype: {dtype}")

        data = np.fromfile(filename, dtype=dtype)
        data = toFloat(data)
        if IQfile:
            data = data.view(np.complex)

    return rate, data

def writeFile(data, filename, dtype, rate=None, wavFile=False):
    if wavFile and not rate:
        raise ValueError("wavFile must be used with rate")

    dtype = np.dtype(dtype)
    if dtype not in validDTypes:
        raise ValueError(f"Unsupported dtype: {dtype}")

    if dtype == np.complex:
        if wavFile:
            raise TypeError("Can't write complex data to WAV file")
        if data.dtype != np.complex:
            raise TypeError("Can't write real data to complex file")
        data.tofile(filename, dtype=np.complex64)
    else:
        if data.dtype == 'complex':
            if wavFile:
                I = fromFloat(data.real, dtype)
                Q = fromFloat(data.imag, dtype)
                data = np.column_stack(I, Q)
                wavfile.write(filename, rate, data)
            else:
                data = interleaveComplex(data)
                data = fromFloat(data, dtype)
                data.tofile(filename)
        else:
            data = fromFloat(data, dtype)
            if wavFile:
                wavfile.write(filename, rate, data)
            else:
                data.tofile(filename, dtype=dtype)
