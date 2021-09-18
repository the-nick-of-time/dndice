#! /usr/bin/env python3
# Modified from https://gist.github.com/tmonjalo/33c4402b0d35f1233020bf427b5539fa
"""
List all Firefox tabs with title and URL
Supported input: json or jsonlz4 recovery files
Default output: title (URL)
Output format can be specified as argument
"""

import sys
import pathlib
import lz4.block
import json

path = pathlib.Path.home().joinpath('.mozilla/firefox')
files = path.glob('*default*/sessionstore-backups/recovery.js*')

for f in files:
    b = f.read_bytes()
    if b[:8] == b'mozLz40\0':
        b = lz4.block.decompress(b[8:])
    j = json.loads(b)
    for w in j['windows']:
        for t in w['tabs']:
            i = t['index'] - 1
            print(t['entries'][i]['url'])