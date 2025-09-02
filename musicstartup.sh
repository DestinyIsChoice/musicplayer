#!/bin/bash

# Detect operating system.
if [ $(ps -ef|grep -c com.termux ) -gt 0 ]; then

    # Install dependencies.
    yes | pkg i python
    yes | pkg i x11-repo
    yes | pkg i sdl2 sdl2-gfx sdl2-image sdl2-mixer sdl2-ttf
    yes | pkg i xorgproto
    yes | pkg i ffmpeg
    pip install -r requirements.txt

    # Stop operating system from closing Termux.
    termux-wake-lock

    # Patch PulseAudio in order to allow for audio to be played.
    SCRIPT_DIR=$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")
    rm -f /data/data/com.termux/files/usr/etc/pulse/default.pa
    cp "$SCRIPT_DIR/default.pa" /data/data/com.termux/files/usr/etc/pulse/

    # Clear console and run music player.
    cd $SCRIPT_DIR
    clear
    export PYGAME_HIDE_SUPPORT_PROMPT="1"
    python "$SCRIPT_DIR/musicplayer.py"
else

    # Install dependencies.
    pip install -r requirements.txt

    # Clear console and run music player.
    clear
    export PYGAME_HIDE_SUPPORT_PROMPT="1"
    python musicplayer/musicplayer.py
fi
