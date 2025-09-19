#!/bin/bash

# Detect operating system.
if echo "$PREFIX" | grep -q "com.termux"; then

    # Install dependencies.
    yes | pkg i python
    yes | pkg i x11-repo
    yes | pkg i sdl2 sdl2-gfx sdl2-image sdl2-mixer sdl2-ttf
    yes | pkg i xorgproto
    yes | pkg i ffmpeg

    # Stop operating system from closing Termux.
    termux-wake-lock

    # Patch PulseAudio in order to allow for audio to be played.
    rm -f /data/data/com.termux/files/usr/etc/pulse/default.pa
    cp "musicplayer/default.pa" /data/data/com.termux/files/usr/etc/pulse/
fi

    # Unpack dependencies.
    cd musicplayer || return
    unzip -d libs libs.zip
    rm -f libs.zip

    # Clear console and run music player.
    git pull origin main
    clear
    export PYTHONPATH="$PWD/libs:$PYTHONPATH"
    export PYTHONIOENCODING=utf-8
    export PYGAME_HIDE_SUPPORT_PROMPT="1"
    python musicplayer.py
