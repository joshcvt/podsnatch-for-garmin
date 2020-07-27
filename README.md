# PodSnatch for Garmin

PodSnatch is a simple<sup>[1](#footnote1)</sup>, cross-platform
<sup>[2](#footnote2)</sup> podcast downloader that pulls MP3 files and prepares them to appear
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

--Josh Crockett
  josh.crockett@gmail.com
  https://github.com/joshcvt

<a name="footnote1">1</a>: Only (originally) \~100 lines of Python!

<a name="footnote2">2</a>: *Probably*, I've only tested on Mac.

## Usage
```# First time
pip install < requirements.txt

# after that, just run this every time
python podsnatch.py --opml <input file> -o <output directory>
```

## Optional parameters: 

`-n 5` downloads only the most recent 5 (or whatever number you change 
it to) episodes.
`--output-metadata`: If you want text metadata for each episode in a plaintext
file with the same name as the episode audio, with `.txt` appended, use this once I get 
that parameter working again. The original version did this 
automatically, but the Garmin use case didn't have much need for the text files so I 
disabled it.

## Docker

If you don't want to deal with all the python setup crap (and I don't blame you)
the original author says you can build the docker container and run with

```bash
docker run -it -v '/path/to/opml.opml:/input.opml' -v '/path/to/output_dir:/output' podsnatch
```

I haven't tested that, but I'm leaving his Dockerfile intact in case it helps someone.

## Contributing
PRs welcome!
