# sf2_to_dex

Python tool to extract WAV files from .sf2 (SoundFont®) files in a format optimised for the [disting EX](https://expert-sleepers.co.uk/distingEX.html) SD Multisample algorithm


<h3>Usage</h3>
Be sure to located sf2 files are in same directory with this script.

```python
python sf2_to_dex.py fileToExtract.sf2
```

<h3>Dependencies</h3>

[https://pypi.org/project/chunkmuncher/](https://pypi.org/project/chunkmuncher/)

Previously we used the standard Python 'chunk' module, which was inexplicably deprecated and removed from Python 3.13.0.
