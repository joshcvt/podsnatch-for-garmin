#! /usr/bin/env python

from lxml import etree as xml
from tqdm import tqdm
import feedparser
import requests
import argparse
import signal
import time
import sys
import re
import os
import traceback

from pathvalidate import sanitize_filename

import eyed3
from eyed3.id3 import ID3_V2_4

# longterm: https://github.com/akallabeth/python-mtp to deliver the files directly

TMP_EXT = '.part'
RETIRE_FILENAME = 'retired_paths.txt'


class Show:

  def __init__(self, outline_element):
    self.title = outline_element.get('text')
    self.url = (outline_element.get('xmlUrl') or
                outline_element.get('xmlurl') or
                None)
    self.episode_guids = []

  def __str__(self):
    return f'{self.title}: {self.url}'

  def get_dir_name(self):
    return sanitize_filename(self.title)


class Episode:

  def __init__(self, item, show):
    self.guid = item.id if 'id' in item else ''
    self.title = item.title if 'title' in item else ''
    self.link = item.link if 'link' in item else ''
    self.description = item.summary if 'summary' in item else ''
    self.content = item.content[0].value if 'content' in item else ''
    self.number = item.itunes_episode if 'itunes_episode' in item else ''
    self.url = item.enclosures[0].href if 'enclosures' in item and item.enclosures else ''
    self.date = item.published_parsed if 'published_parsed' in item else ''

    self.show = show

  def __str__(self):
    return f"""{self.title}
{self.number}
{self.guid}
{self.date}
{self.link}
{self.url}
{self.content if self.content else self.description}
{self.description}"""

  def get_file_name(self):
    return sanitize_filename(self.title) + '.' + self.url.split('.')[-1].split('?')[0]


def parse_opml(opml_path):
  tree = xml.parse(opml_path)
  root = tree.getroot()

  shows = root.findall('./body/outline')

  return [Show(x) for x in shows]


def download(url, path, mode):
  # https://stackoverflow.com/a/37573701
  response = requests.get(url, stream=True)
  total_size = int(response.headers.get('content-length', 0))
  block_size = 1024

  t = tqdm(total=total_size, unit='iB', unit_scale=True)
  with open(path, mode) as f:
    for data in response.iter_content(block_size):
      t.update(len(data))
      f.write(data)
  t.close()

  if total_size != 0 and t.n != total_size:
    print("ERROR downloading file")


total_downloaded = 0
full_path = ''


def save_podcasts(opml, output, episode_count=None, episode_meta=False, use_flat_directory=False, retired_files=[],dnm=False):
  global total_downloaded
  global full_path

  shows = parse_opml(opml)

  for show in shows:
    print(f'Processing show {show.title}')
    feed = feedparser.parse(show.url)

    if use_flat_directory:
        show_path = output
    else:
        show_path = os.path.join(output, show.get_dir_name())
    os.makedirs(show_path, exist_ok=True)

    cnt_eps_to_dl = (int(episode_count, 10)
                     if episode_count is not None
                     else len(feed.entries))

    i = (cnt_eps_to_dl if len(feed.entries) > cnt_eps_to_dl else len(feed.entries))
    show_downloaded = 0
    
    while i > 0:
      i -= 1
      item = feed.entries[i]
      episode = Episode(item, show)

      if use_flat_directory:
        full_path = os.path.join(show_path, show.get_dir_name() + " - " + episode.get_file_name())
      else:
        full_path = os.path.join(show_path, episode.get_file_name())
      print(f'Processing {full_path}: ',end="")

      if (full_path in retired_files):
        print('Episode retired.')
        
      elif episode.url and not os.path.exists(full_path):
        print('Downloading episode')
        download(episode.url, full_path + TMP_EXT, 'wb')

        os.rename(full_path + TMP_EXT, full_path)
        
        if not dnm:
          do_munge(full_path,show.title,episode.title,feed['feed']['author'])
        else:
          print("Warning: did not munge " + full_path)

        if episode_meta:
          handle = open(full_path + ".txt", "w")
          handle.write(str(episode))
          handle.close()

        total_downloaded += 1
      else:
        print('Episode already downloaded!')

      show_downloaded += 1

  print(f'{total_downloaded} episodes downloaded')


def do_munge(full_path,show_title,episode_title,feed_author):

  try:
    audiofile = eyed3.load(full_path)
  except:
    print("EyeD3 load exception on: " + full_path)
    return
  if not audiofile:
    print("EyeD3 returned null loading: " + full_path)
    return

  if not audiofile.tag:
    audiofile.tag = eyed3.id3.Tag()
    audiofile.tag.version = ID3_V2_4

  if audiofile.tag.version != ID3_V2_4:
    audiofile.tag.version = ID3_V2_4
  audiofile.tag.album = show_title
  audiofile.tag.title = episode_title
  if ((not audiofile.tag.artist) or (len(audiofile.tag.artist) == 0)):
    audiofile.tag.artist = feed_author
  audiofile.tag.album_artist = feed_author
  audiofile.tag.track_num = None
  audiofile.tag.genre = 186
  try:
    audiofile.tag.save()
  except UnicodeEncodeError:
    # this generally happens when eyeD3 thinks everything has to be latin-1 for some reason. so force the tags and resave.
    print("Forcing text tags to latin-1")
    audiofile.tag.album = audiofile.tag.album.encode("latin-1","ignore")
    audiofile.tag.title = audiofile.tag.title.encode("latin-1","ignore")
    audiofile.tag.artist = audiofile.tag.artist.encode("latin-1","ignore")
    audiofile.tag.album_artist = audiofile.tag.album_artist.encode("latin-1","ignore")
    try:
      audiofile.tag.save()
    except:
      print("Second save failed, stuck with original tags")


def retire_file(path,retire_file_path,do_delete):
  
  existing = load_retired(retire_file_path)
  if path in existing:
    print("already retired " + path)
  else:
    existing.append(path)
    if not retire_file_path:
      retire_file_path = RETIRE_FILENAME
    with open(retire_file_path,"w") as rfl:
      rfl.writelines(line + '\n' for line in existing)
  if do_delete:
    os.unlink(path)
  return

def load_retired(retire_fn=False):
  if not retire_fn:
    retire_fn = RETIRE_FILENAME
  fns = []
  try:
    with open(retire_fn) as rfl:
      lines = rfl.readlines()
    for ln in lines:
      fns.append(ln.strip())
  except FileNotFoundError:
    pass
  except Exception as ex:
    traceback.print_exc()
  
  return fns

def ctrl_c_handler(signum, frame):
  print('Stopping...')

  if os.path.exists(full_path + TMP_EXT):
    os.remove(full_path + TMP_EXT)

  print(f'{total_downloaded} episodes downloaded')
  sys.exit(1)


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Download podcasts.')
  group = parser.add_mutually_exclusive_group(required=True)
  group.add_argument('--opml', '-i', dest='opml_loc', action='store',
                      help='path to opml file to import')
  group.add_argument('--retire','-r',dest='retire',action='store',
                      help='path to file to retire as listened (so it won\'t be downloaded again) and delete')
  group.add_argument('--retire_safe','-s',dest='retire_safe',action='store',
                      help='path to file to retire (but not delete)')
  parser.add_argument('--output-dir', '-o', dest='output_loc', action='store',
                      required=False, default='.',
                      help='location to save podcasts')
  parser.add_argument('--flat',action="store_true",help="use flat directory structure")
  parser.add_argument('--number-of-episodes', '-n', dest='ep_cnt',
                      action='store', default=None,
                      help='Download at most the last n episodes in the feed')
  parser.add_argument('--metadata',action="store_true", 
                      help="Output .txt metadata file for each episode")
  parser.add_argument('--retire_filename',dest="retire_fn",action='store',default=None,
                      help="Path to textfile containing paths to treat as already downloaded")
  parser.add_argument('--open_if_new','-ifn',action="store_true",required=False,help="open the output directory in Finder if there were new episodes")
  parser.add_argument('--dnm',action="store_true",required=False,help="do not munge the tags (i.e. get files for debugging)")
  args = parser.parse_args()

  signal.signal(signal.SIGINT, ctrl_c_handler)

  if args.retire:
    retire_file(args.retire,args.retire_fn,True)
  elif args.retire_safe:
    retire_file(args.retire_safe,args.retire_fn,False)
  else:
    retired_files = load_retired(args.retire_fn)
    save_podcasts(args.opml_loc, args.output_loc, args.ep_cnt, args.metadata, args.flat, retired_files, args.dnm)
    
  if total_downloaded > 0 and args.open_if_new and args.output_loc:
    os.system("open " + args.output_loc)
