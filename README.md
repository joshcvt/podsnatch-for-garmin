# PodSnatch for Garmin

PodSnatch is a simple, cross-platform
<sup>[1](#footnote2)</sup> podcast downloader that pulls MP3 files and prepares them to appear
sanely on a Garmin watch.  Mac users cannot count on this in Catalina or after
(even when Garmin's services are working) due to Apple exploding iTunes and replacing the
podcasts element with a half-baked, iOS-derived app that strips *all* metadata from the
MP3 files and hides those files deep in the Library directory structure.

The guts of it (actually going and getting the MP3 files) 
are based on [PodSnatch](https://github.com/robotmlg/podsnatch) by [Matt 
Goldman](https://github.com/robotmlg), who I thank for publishing his work for people 
like me to mooch off of.

Once you have the MP3 files, you can copy them to /Podcasts on the Media partition 
of your watch using Android File Transfer. I'd love to build in MTP eventually to do it 
automatically, but no promises.

--Josh Crockett ([mail](mailto:josh.crockett@gmail.com)/[GH](https://github.com/joshcvt))

<a name="footnote2">1</a>: *Probably*, I've only tested on Mac.

## Usage
```# First time
pip install < requirements.txt

# To get all episodes of all podcasts into output_dir/podcast_name/podcast_name - episode_title.mp3
python podsnatch.py --opml <input file> -o <output directory>
```

## Optional parameters: 

* `-n 5` downloads only the most recent 5 (or whatever number you change 
it to) episodes.
* `--flat` puts downloads into a single flat directory as output_dir/podcast_name - episode_title.mp3
* `-r output_dir/file.mp3` *retires* a file: deletes it and puts it into `retired_paths.txt` so it won't be re-downloaded. This is how I mark episodes as done.

## Docker

If you don't want to deal with setting up a Python environment (and I don't blame you)
the original author says you can build the docker container and run with

```bash
docker run -it -v '/path/to/opml.opml:/input.opml' -v '/path/to/output_dir:/output' podsnatch
```

I haven't tested that, but I'm leaving his Dockerfile intact in case it helps someone.

## Contributing
PRs welcome!
