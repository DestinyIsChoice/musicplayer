# musicplayer
Ultra lightweight python music player.

The dependencies are as follows:

> inputimeout  
> mutagen  
> pygame  
> youtube-search  
> yt_dlp  

Running the music player on Termux requires more dependencies:

> python  
> x11-repo  
> sdl2  
> sdl2-gfx  
> sdl2-image  
> sdl2-mixer  
> sdl2-ttf  
> xorgproto  
> ffmpeg  

In order to run the music player if you are not using Termux:

* First use setup:
  * Install the dependencies using pip *(ex. `pip install inputimeout`)*

* Normal use:
  * Run musicplayer.py  

In order to run the music player on Termux:

* First use setup:
  * Use `termux-setup-storage` and allow Termux to access files using the slider
  * Install git using `pkg i git`
  * Clone the repository using `git clone https://github.com/DestinyIsChoice/musicplayer.git`
  * Enter the musicplayer folder using `cd musicplayer`
  * Open the startup script using `bash musicstartup.sh`

* Normal use:
  * Open the startup script using `bash musicplayer/musicstartup.sh`
