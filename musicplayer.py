import json
import os
from os import environ
import random
import shutil
import sys


# Stops pygame from sending initial message
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'


from inputimeout import inputimeout
from mutagen.mp3 import MP3
import pygame
from youtube_search import YoutubeSearch
import yt_dlp as youtube_dl


path = ""


def get_path():
    """Validates a user input as a folder containing music.

    Will prompt user for a new input if previous was not a folder containing music.
    """

    # Validates user input as a folder containing music by having user input again if not a folder containing music.
    global path
    path = input("→ Please input the path to your music folder!\n→ ")
    while True:
        if os.path.isdir(path):
            if len(os.listdir(path)) == 0:
                print("→ This folder currently contains no music! ")
        else:
            os.mkdir(path)
            print("→ This folder currently contains no music! ")
        break


def validate_int():
    """Validates a user input as an integer.

    Will prompt user for a new input if previous could not be transformed into an integer.
    """

    # Validates input as an integer by having user input again if not transformable to integer.
    validated_string = input("→ ")
    while True:

        # Allows user to select a song if selecting is cancelled.
        if validated_string == "-":
            main(input("→ "))

        # Validates user input as integer
        else:
            try:
                validated_string = int(validated_string)
                return validated_string
            except:
                validated_string = input("→ ")


def clean(string):
    """Removes illegal characters from a string used as a file name.
    """

    return string.translate(str.maketrans('', '', '"/\\<>*:|?'))


def get_audio(options, index, folder, name):
    """Downloads audio from YouTube.

    Uses silent output.

    Uses ffmpeg to get mp3 file.
    """
    try:
        os.remove(f"{folder}/{name}.mp3")
    except:
        pass

    # Silences output by redirecting stdout to nothing.
    old_stdout = sys.stdout
    sys.stdout = open(os.devnull, "w")

    # Downloads audio from YouTube as mp3 using ffmpeg.
    with youtube_dl.YoutubeDL({
        'format': 'bestaudio/best',
        'outtmpl': f"{folder}/{name}",
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'
        }]
    }) as ydl:
        ydl.download([f"https://www.youtube.com/watch?v={options["videos"][index - 1]["id"]}"])

    # Redirects stdout back to command line.
    sys.stdout = old_stdout


def allow_pausing(current):
    """Prompts user for an input.

    User will now be able to pause currently playing music.

    Will call itself again in order to allow pausing if music is unpaused.
    """

    try:
        audio = MP3(current)

        # Checks if music is being streamed
        if (((current.split("/"))[(len(current.split("/"))) - 1]).replace(".mp3", "")) == "file":
            print("→ Now playing streamed music!")
        else:
            print(f"→ Now playing {((current.split("/"))[(len(current.split("/"))) - 1]).replace(".mp3", "")}!")

        # Allows for user input
        pausable = inputimeout(prompt="→ ", timeout=(audio.info.length - (pygame.mixer.music.get_pos() / 1000)))
    except:
        pausable = "_"

    # Checks if user intends to pause music, skip song or select a new song.
    if pausable == "/":
        pygame.mixer.music.pause()
        pausable = input("→ (Music paused!) ")
        if pausable:
            pygame.mixer.music.unpause()
            allow_pausing(current)
    elif pausable == "_":
        return
    else:
        main(pausable)


def main(initial_input):
    """Handles initial user input.

    Takes user input and creates a list of songs.

    Downloads songs which are marked for downloading and uses local files otherwise.

    List of songs contains user specified order followed by a random assortment of local files.
    """

    global path
    downloaded = False
    downloaded_name = ""

    # Handles exiting the program.
    if initial_input == "\\":
        pygame.mixer.quit()
        shutil.rmtree(f"{path}/temp")
        print("→ Exiting! ")
        exit(0)
    elif initial_input == "_":
        main(input("→ "))
    # Handles streaming an audio file from YouTube.
    if initial_input == initial_input.replace("_", ""):
        if initial_input == "-":
            try:
                youtube_results = json.loads(YoutubeSearch(input("→ "), max_results=10).to_json())
                for number, video in enumerate(youtube_results["videos"]):
                    print(f"→ {number + 1}.", video["title"])
                input_number = validate_int()

                # Downloads temporary audio file from YouTube.
                get_audio(youtube_results, input_number, path, "temp/file")
                downloaded = True

            # Sends an error message and allows user to select a song if streaming fails.
            except:
                print("→ Could not connect to server!")
                main(input("→ "))

        # Handles downloading an audio file from YouTube.
        elif initial_input == "'":
            try:
                youtube_results = json.loads(YoutubeSearch(input("→ "), max_results=10).to_json())
                for number, video in enumerate(youtube_results["videos"]):
                    print(f"→ {number + 1}.", video["title"])
                input_number = validate_int()

                # Downloads audio file from YouTube
                title = clean(youtube_results["videos"][input_number - 1]["title"])
                get_audio(youtube_results, input_number, path, title)
                downloaded_name = f"{title}.mp3"

            # Sends an error message and allows user to select a song if downloading fails.
            except:
                print("→ Could not connect to server!")
                main(input("→ "))

        # Creates variables for creating list of songs to be played.
        all_songs = []
        intended_songs = [""] if (downloaded == True) else []
        input_characters = list((initial_input.split(" "))[0])

        # Finds characters to match to user input.
        for song in os.listdir(path):
            all_songs.append(song)
            song_characters = []
            song_words = song.split(" ")
            if len(song_words) > 1:
                for word in song_words:
                    song_characters.append(((list(word))[0]).lower())
            else:
                song_characters = list((song.split(".mp3"))[0])
            song_characters = [character.lower() for character in song_characters]

            # Checks if user input matches song.
            counter = 0
            for letter in list(input_characters):
                if letter in song_characters:
                    counter += 1
            if counter == len(list(input_characters)):
                intended_songs.append(song)

        # Removes temp folder from list of songs to be played.
        if "temp" in intended_songs:
            intended_songs.remove("temp")

        # Prompts user for which song to play if multiple songs match user input.
        if len(intended_songs) > 0:
            if len(intended_songs) > 1:
                if (downloaded == False) and (downloaded_name == ""):
                    try:
                        int((initial_input.split(" "))[1])
                        no_index = False
                    except:
                        no_index = True
                    if (len(initial_input.split(" ")) == 1) or no_index:
                        for number, playable_song in enumerate(intended_songs):
                            print(f"→ {number + 1}.", playable_song[:-4])
                        index = validate_int()

                    # Accounts for if user has already selected which song to play if multiple songs match input.
                    else:
                        index = int((initial_input.split(" "))[1])

                # Initializes music player and creates list of songs to be played.
                pygame.mixer.init()
                if "temp" in all_songs:
                    all_songs.remove("temp")
                random.shuffle(all_songs)

                # Adds streamed and downloaded songs to list of songs to be played.
                if downloaded_name != "":
                    all_songs.insert(0, downloaded_name)
                elif not downloaded:
                    try:
                        specific_song = intended_songs[index - 1]
                        all_songs.remove(specific_song)
                        all_songs.insert(0, specific_song)
                    except:
                        print("→ This song cannot be played!")
                        main(input("→ "))
                else:
                    all_songs.insert(0, "temp/file.mp3")

                # Plays songs in list of songs to be played.
                for playable_song in all_songs:
                    pygame.mixer.music.load(f"{path}/{playable_song}")
                    pygame.mixer.music.play()

                    # Allows user to pause music.
                    if downloaded_name != "":
                        allow_pausing(f"{path}/{downloaded_name}")
                        downloaded_name = ""
                    elif downloaded:
                        allow_pausing(f"{path}/{playable_song}")
                    else:
                        allow_pausing(f"{path}/{playable_song}")
                get_path()
                main(input("→ "))

            # Initializes music player and creates list of songs to be played.
            else:
                pygame.mixer.init()
                if "temp" in all_songs:
                    all_songs.remove("temp")
                random.shuffle(all_songs)

                # Adds streamed and downloaded songs to list of songs to be played.
                if downloaded_name != "":
                    all_songs.insert(0, downloaded_name)
                elif not downloaded:
                    all_songs.remove(intended_songs[0])
                    all_songs.insert(0, intended_songs[0])
                else:
                    all_songs.insert(0, "temp/file.mp3")

                # Plays songs in list of songs to be played.
                for playable_song in all_songs:
                    pygame.mixer.music.load(f"{path}/{playable_song}")
                    pygame.mixer.music.play()

                    # Allows user to pause music.
                    if downloaded_name != "":
                        allow_pausing(f"{path}/{downloaded_name}")
                        downloaded_name = ""
                    elif downloaded:
                        allow_pausing(f"{path}/{playable_song}")
                    else:
                        allow_pausing(f"{path}/{playable_song}")
                get_path()
                main(input("→ "))

        # Allows user to select music to play if none is found.
        else:
            if (initial_input != "-") and (initial_input != "'"):
                print("→ No music found!")
            main(input("→ "))

    # Creates shuffled list of music to be played.
    else:
        all_songs = []
        for song in os.listdir(path):
            all_songs.append(song)
        random.shuffle(all_songs)

        # Handles each song in user input separately.
        counter = 0
        for song in initial_input.split("_"):
            intended_songs = []
            for individual_input in song.split("_"):
                input_characters = list((individual_input.split(" "))[0])
                if input_characters[0] != "-":
                    for inputs in os.listdir(path):
                        song_characters = []
                        song_words = inputs.split(" ")
                        if len(song_words) > 1:
                            for word in song_words:
                                song_characters.append(((list(word))[0]).lower())
                        else:
                            song_characters = list((inputs.split(".mp3"))[0])
                        song_characters = [s.lower() for s in song_characters]
                        matching_characters = 0
                        for letter in list(input_characters):
                            if letter in song_characters:
                                matching_characters += 1

                        # Adds song to list of songs to be played if it matches user input.
                        if matching_characters == len(list(input_characters)):
                            intended_songs.append(inputs)

                    # Removes temp folder from list of songs to be played.
                    if "temp" in intended_songs:
                        intended_songs.remove("temp")

                    # Prompts user for which song to play if multiple songs match user input.
                    if len(intended_songs) > 0:
                        if len(intended_songs) > 1:
                            try:
                                int((individual_input.split(" "))[1])
                                no_index = False
                            except:
                                no_index = True
                            if no_index:
                                for number, playable_song in enumerate(intended_songs):
                                    print(f"→ {number + 1}.", playable_song[:-4])
                                index = validate_int()

                            # Accounts for if user has already selected which song to play if multiple songs match input. # noqa
                            else:
                                index = int((individual_input.split(" "))[1])

                            # Moves song to be played to front of list of songs to be played.
                            specific_song = intended_songs[index - 1]
                            all_songs.remove(specific_song)
                            all_songs.insert(counter, specific_song)
                        else:
                            specific_song = intended_songs[0]
                            all_songs.remove(specific_song)
                            all_songs.insert(counter, specific_song)
                else:
                    try:
                        youtube_results = json.loads(YoutubeSearch(individual_input.replace("-", ""),
                                                                   max_results=1).to_json())
                        name = youtube_results["videos"][0]["title"]
                        print(f"→ Now downloading {name}! ")
                        title = f"temp/{clean(name)}"
                        get_audio(youtube_results, 0, path, title)
                        all_songs.insert(counter, f"{title}.mp3")

                    # Sends an error message and allows user to select a song if downloading fails.
                    except:
                        print("→ Could not connect to server!")
                        main(input("→ "))

            # Moves onto next position in list of songs to be played.
            counter += 1

        # Removes temp folder from list of songs to be played.
        pygame.mixer.init()
        if "temp" in all_songs:
            all_songs.remove("temp")

        # Plays songs in list of songs to be played.
        for playable_song in all_songs:
            pygame.mixer.music.load(f"{path}/{playable_song}")
            pygame.mixer.music.play()
            allow_pausing(f"{path}/{playable_song}")
        get_path()
        main(input("→ "))


get_path()
main(input("→ "))
