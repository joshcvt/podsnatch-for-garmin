#! /usr/bin/env python

from mp3_tagger import MP3File, VERSION_1, VERSION_2, VERSION_BOTH
from pathlib import Path

pathlist = Path("dls").rglob('*.mp3')
for path in pathlist:
    # because path is object not string
    path_in_str = str(path)
    # Create MP3File instance.
    
    mp3 = MP3File(path_in_str)
    print(path_in_str)
    try:
        print(mp3.get_tags())
    except:
        pass
    print("")  # blank ln plz
