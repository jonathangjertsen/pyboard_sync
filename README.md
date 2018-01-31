# Pyboard Sync

This script keeps files on a MicroPython Pyboard in sync with a directory on your
computer. Run it in the background while working on your files, and the Pyboard
is automatically flashed to run the new code. Works well with auto-saving
editors such as PyCharm.

## Installation

Clone this project and open its directory. Then, in a Python 3.6+ environment,
run:

```
pip install -r requirements.txt
```

Of course, you also need a Pyboard to be plugged in.

## Usage

### Example
I keep most of my Python projects in a directory, and the one with the source
code for the pyboard is called `upython`. When the pyboard is plugged in, it has
the drive letter F:/, and it appears as COM4 in Device Manager. Therefore I open
 a shell and run:

```
python pyboard_flasher/watch.py upython F --port COM4
```

and whenever something changes in the `upython` directory, the changed files are
uploaded to the pyboard and the board is rebooted to include the new changes.

### Full output of `watch.py -h`:

```
usage: watch.py [-h] [-v] [-r] [-p PORT] [-m MAIN] path drive

Watch a directory and flash the pyboard

positional arguments:
  path                  The path to watch
  drive                 The drive letter of the pyboard

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         If set, all actions are logged to the console
                        (default=TRUE)
  -r, --reboot          If set, soft reboot board on save (default=TRUE)
  -p PORT, --port PORT  Serial port for the pyboard (e.g. COM4)
  -m MAIN, --main MAIN  Main file referenced by boot.py (typically main.py)
```
