#! /usr/bin/env python

#from mp3_tagger import MP3File, VERSION_1, VERSION_2, VERSION_BOTH
from pathlib import Path
import eyed3
import traceback

# https://stackoverflow.com/questions/10377998/how-can-i-iterate-over-files-in-a-given-directory
pathlist = Path("dls/debug/").rglob('*.mp3')
for path in pathlist:
    # because path is object not string
    path_in_str = str(path)

    print(path_in_str)
    try:
        audiofile = eyed3.load(path_in_str)
        if audiofile:
            print(str(audiofile.tag))
            print(audiofile.tag.version)
            print(audiofile.tag.album)
            print(audiofile.tag.title)
            print(audiofile.tag.artist)
            print(audiofile.tag.album_artist)
            print(audiofile.tag.track_num)
            print(audiofile.tag.genre)
    except Exception as ex:
        traceback.print_exc()
    print("")  # blank ln plz
