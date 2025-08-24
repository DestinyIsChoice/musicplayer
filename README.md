# Setup and Usage

In order to run the music player outside of Termux:

* First use setup:

        git clone https://github.com/DestinyIsChoice/musicplayer.git
        pip install inputimeout  
        pip install mutagen  
        pip install pygame  
        pip install pytube  
        pip install pytubefix  
        pip install youtube-search  
        pip install yt_dlp  
        python musicplayer/musicplayer.py  

* Normal use:

      python musicplayer/musicplayer.py  

In order to run the music player in Termux:

* First use setup:

      termux-setup-storage # Allow Termux to access files using the slider.
      pkg i git
      git clone https://github.com/DestinyIsChoice/musicplayer.git
      bash musicplayer/musicstartup.sh

* Normal use:

      bash musicplayer/musicstartup.sh
