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

from pathvalidate import sanitize_filename

#mp3_tagger is unreliable, don't do it
#from mp3_tagger import MP3File, VERSION_1, VERSION_2, VERSION_BOTH
import eyed3
from eyed3.id3 import ID3_V2_4

# longterm: https://github.com/akallabeth/python-mtp to deliver the files directly

TMP_EXT = '.part'


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
    # preserving old code below
    url_tail = self.url.split('/')[-1].split('?')[0]
    show_title = re.sub(r'[\W]+', '_', self.show.title)
    ep_title = re.sub(r'[\W]+', '_', self.title)
    formatted_date = time.strftime('%Y_%m_%d', self.date)

    name_tokens = [formatted_date, self.number, ep_title, url_tail]
    return '_'.join([s for s in name_tokens if s is not ''])


def parse_ompl(ompl_path):
  tree = xml.parse(ompl_path)
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


def save_podcasts(opml, output, episode_count=None, episode_meta=False, use_flat_directory=False):
  global total_downloaded
  global full_path

  shows = parse_ompl(opml)

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

    i = 0
    show_downloaded = 0
    while show_downloaded < cnt_eps_to_dl and i < len(feed.entries):
      item = feed.entries[i]
      episode = Episode(item, show)

      if use_flat_directory:
        full_path = os.path.join(show_path, show.get_dir_name() + " - " + episode.get_file_name())
      else:
        full_path = os.path.join(show_path, episode.get_file_name())
      print(f'Processing episode {episode.title} to {full_path}')

      if not os.path.exists(full_path) and episode.url:
        print('Downloading episode')
        download(episode.url, full_path + TMP_EXT, 'wb')

        os.rename(full_path + TMP_EXT, full_path)
        
        audiofile = eyed3.load(full_path)
        
        if audiofile.tag.version != ID3_V2_4:
          audiofile.tag.version = ID3_V2_4
        audiofile.tag.album = show.title
        audiofile.tag.title = episode.title
        if ((not audiofile.tag.artist) or (len(audiofile.tag.artist) == 0)):
            audiofile.tag.artist = feed['feed']['author']
        audiofile.tag.album_artist = feed['feed']['author']
        audiofile.tag.track_num = None
        audiofile.tag.genre = 186
        audiofile.tag.save()

        if episode_meta:
          handle = open(full_path + ".txt", "w")
          handle.write(str(episode))
          handle.close()

        show_downloaded += 1
        total_downloaded += 1
      else:
        print('Episode already downloaded!')
        show_downloaded += 1

      i += 1

    print(f'{total_downloaded} episodes downloaded')


def ctrl_c_handler(signum, frame):
  print('Stopping...')

  if os.path.exists(full_path + TMP_EXT):
    os.remove(full_path + TMP_EXT)

  print(f'{total_downloaded} episodes downloaded')
  sys.exit(1)


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Download podcasts.')

  parser.add_argument('--opml', '-i', dest='opml_loc', action='store',
                      required=True, help='path to opml file to import')
  parser.add_argument('--output-dir', '-o', dest='output_loc', action='store',
                      required=False, default='.',
                      help='location to save podcasts')
  parser.add_argument('--flat',action="store_true",help="use flat directory structure")
  parser.add_argument('--number-of-episodes', '-n', dest='ep_cnt',
                      action='store', default=None,
                      help='Download at most the last n episodes in the feed')
  parser.add_argument('--metadata',action="store_true", 
                      help="Output .txt metadata file for each episode")
  args = parser.parse_args()

  signal.signal(signal.SIGINT, ctrl_c_handler)

  save_podcasts(args.opml_loc, args.output_loc, args.ep_cnt, args.metadata, args.flat)
