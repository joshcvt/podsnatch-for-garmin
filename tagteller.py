#! /usr/bin/env python

#from mp3_tagger import MP3File, VERSION_1, VERSION_2, VERSION_BOTH
from pathlib import Path
import eyed3
import traceback

# https://stackoverflow.com/questions/10377998/how-can-i-iterate-over-files-in-a-given-directory
pathlist = Path("dls/Forgotten_Stories_of_Football").rglob('*.mp3')
for path in pathlist:
    # because path is object not string
    path_in_str = str(path)

    print(path_in_str)
    try:
        afile = eyed3.load(path_in_str)
        if afile:
            print(str(afile.tag))
    except Exception as ex:
        traceback.print_exc()
    print("")  # blank ln plz
