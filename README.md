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

* Install the dependencies using pip *(ex. `pip install inputimeout`)*  
* Run musicplayer.py  

In order to run the music player on Termux:

* First use setup:
  * Use `termux-setup-storage` and allow Termux to access files using the slider
  * Install git using `pkg i git`
  * Clone the repository using `git clone https://github.com/DestinyIsChoice/musicplayer.git`
  * Enter the musicplayer folder using `cd musicplayer`

* Open the startup script using bash `musicstartup.sh`

Once the music player is running:

* If you have a folder with music:  
    Enter the path in order to access music from the folder  
  
* If you do not have a folder with music in it:  
    Enter a path where you would like to create a music folder  

Once you have selected your music folder you may use any of the following commands  

Commands:  

  In order to use a command, simply enter the command into the console

  * `_` Skip to the next song  
  * `/` Pause the song  
  * `\` Quit the music player  
  * `'` Download music; after using this command, enter in your search, then enter the number corresponding to the search result which you would like to download; if you would like to cancel downloading, enter `-` when you are prompted to enter the corresponding number  
  * `-` Stream music; after using this command, enter in your search, then enter the number corresponding to the search result which you would like to stream; if you would like to cancel streaming, enter `-` when you are prompted to enter the corresponding number  

  Playing music:

  > Each song in your music folder can be played using a short character combination:
  > * If the name of the song is one word:
  >   * You can enter any of the letters in the name without spaces *(ex. if the name of the song was `example`, you could enter the string `xmp` in order to play the song)*
  > * If the name of the song is two or more words:
  >   * You can enter any of the first letters of the words in the name without spaces *(ex. if the name of the song was `example song`, you could enter the string `es` in order to play the song)*
  > * If more than one song in your music folder matches, a menu will appear asking you which song you would like to play. Enter the number corresponding to the song which you would like to play
  >   * If you already know the number corresponding to the song you would like to play, you may place a space after your character combination and add the number before entering *(ex. if `example song` is the sixth option for `es`, you can enter `es 6` in order to bypass the menu)*
  > By default the songs in the music folder will be shuffled. If you would like to play songs in a specific order:
  > * Place `_` in between the character combinations of the songs which you would like to play in the order in which you would like to play them *(ex. if you would like to play `cool song` and then `great music`, you can enter `cs_gm`)*
  > * If you would like to stream music in an order:
  >   * Place `-` at the beginning of a search for music to stream *(ex. if you would like to play `cool song`, then stream a song called `amazing lyrics` and then play `great music`, you can enter `cs_-amazing lyrics_gm`)*
  > * Once the songs have been played in your order, the remaining songs in the music folder will be shuffled and played
  > Once all songs in the music folder have been played, the music player will ask you to select a new music folder

The controls can be very difficult to understand. If you feel that this documentation has not done a good job explaining the music player, feel free to look at the source code and modify it yourself  
This music player was built for speed and efficiency over ease of understanding.
