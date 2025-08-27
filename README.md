# Setup and Usage

In order to run the music player outside of Termux:

* First use setup:

   [Install Git](https://git-scm.com/downloads/win) if you have not already. Then, in Git Bash:  

      git clone https://github.com/DestinyIsChoice/musicplayer.git  
      bash musicplayer/musicstartup.sh  

* Normal use:

      bash musicplayer/musicstartup.sh  

In order to run the music player in Termux:

* First use setup:

      termux-setup-storage # Allow Termux to access files using the slider.  
      pkg i git  
      git clone https://github.com/DestinyIsChoice/musicplayer.git  
      bash musicplayer/musicstartup.sh  

* Normal use:

      bash musicplayer/musicstartup.sh
