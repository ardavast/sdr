# SDR - A place for random SDR experiments

[fm_rx.py](fm_rx.py) - Offline FM receiver written in Python.

Works with files created from SDR#, GQRX, GNU radio file sink, rtl_sdr, etc.

Expects that the sample rate is 1920000.
```
Example usage:
timeout 10 rtl_sdr -f 104e6 -s 1920000 jazzfm.raw
python3 fm_rx.py uint8 jazzfm.raw jazzfm.wav
mplayer jazzfm.wav
```
