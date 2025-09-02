#!/bin/bash

# Detect operating system.
if [ "$( pgrep -c com.termux )" -gt 0 ]; then

    # Install dependencies.
    yes | pkg i python
    yes | pkg i x11-repo
    yes | pkg i sdl2 sdl2-gfx sdl2-image sdl2-mixer sdl2-ttf
    yes | pkg i xorgproto
    yes | pkg i ffmpeg
    pip install -r musicplayer/requirements.txt

    # Stop operating system from closing Termux.
    termux-wake-lock

    # Patch PulseAudio in order to allow for audio to be played.
    rm -f /data/data/com.termux/files/usr/etc/pulse/default.pa
    cp "musicplayer/default.pa" /data/data/com.termux/files/usr/etc/pulse/

    # Clear console and run music player.
    cd musicplayer || return
    clear
    export PYGAME_HIDE_SUPPORT_PROMPT="1"
    python musicplayer.py
else

    # Install dependencies.
    pip install -r musicplayer/requirements.txt

    # Clear console and run music player.
    cd musicplayer || return
    clear
    export PYGAME_HIDE_SUPPORT_PROMPT="1"
    python musicplayer.py
fi
