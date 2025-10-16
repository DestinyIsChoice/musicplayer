"""Ultra lightweight python music player."""


import json
import logging
import os
import pytubefix.exceptions
import random
import shutil
import subprocess
import urllib.request

import eyed3
from eyed3.id3.frames import ImageFrame
from inputimeout import inputimeout, TimeoutOccurred
from mutagen.mp3 import MP3
from PIL import Image
import pygame
import pygame._sdl2.audio
from pytubefix import YouTube, Playlist
from youtube_search import YoutubeSearch


# noinspection SpellCheckingInspection
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
current_audio = ""
current_volume = 100
currently_playing = ""
path = ""
past_position = 0


def clean(string: str) -> str:
    """Removes illegal characters from a string used as a file name."""

    return string.translate(str.maketrans("", "", '\\/:*?"<>|'))


def get_songs(songs_path: str) -> list[tuple]:
    """Gets all songs and albums in a folder."""

    song_list = []

    # Gets all songs.
    for root, albums, songs in os.walk(songs_path):
        for song in songs:
            song_list.append((os.path.join(root, song))
                             .replace("\\", "/").replace(f"{songs_path}/", ""))

    # Gets all albums.
    path_list = ["".join(song.split("/")[:-1]) for song in song_list]
    for number, song_path in enumerate(path_list):
        if song_path != "":
            path_list[number] = f"{song_path}/"
    song_list = [song.split("/")[-1] for song in song_list]

    # Turns songs and albums into a tuple.
    return list(zip(song_list, path_list))


def get_path() -> None:
    """Validates a user input as a folder containing music.

    Will prompt user for a new input

    if previous was not a folder containing music.
    """

    # Validates user input as a folder containing music
    # by having user input again if not a folder containing music.
    global path
    while True:
        path = input("→ Please input the path to your music folder!\n→ ")
        if path == "\\":
            get_path()
            return
        else:
            try:
                if os.path.isdir(path):
                    if not os.listdir(path):
                        print("→ This folder currently contains no music! ")
                    return
            except FileNotFoundError:
                print("→ Cannot open this folder!")
                get_path()
            else:
                if input("→ Would you like to create a new folder? (Y/n)\n→ ") == "n":
                    get_path()
                    return
                else:
                    try:
                        os.mkdir(path)
                    except OSError:
                        get_path()
                    except Exception as e:
                        print(f"→ An error occurred: {e}")
                    return


def validate_int() -> int | None:
    """Validates a user input as an integer.

    Will prompt user for a new input

    if previous could not be transformed into an integer.
    """

    input_time = 2147483647
    try:
        # noinspection PyUnresolvedReferences
        input_time = (current_audio.info.length
                      - pygame.mixer.music.get_pos() / 1000
                      - past_position)
    except (AttributeError, pygame.error):
        pass
    except Exception as e:
        print(f"→ An error occurred: {e}")
    # Validates input as an integer by having user input again
    # if not transformable to integer.
    try:
        validated_string = inputimeout(prompt="→ ", timeout=input_time)
    except TimeoutOccurred:
        return None

    # Allows user to select a song if selecting is cancelled.
    if validated_string == "-":
        try:
            main(inputimeout(prompt="→ ", timeout=input_time))
        except TimeoutOccurred:
            return None
        return None
    while True:

        # Validates user input as integer
        try:
            validated_string = int(validated_string)
            return validated_string
        except ValueError:
            if validated_string == "-":
                try:
                    main(inputimeout(prompt="→ ", timeout=input_time))
                except TimeoutOccurred:
                    return None
                return None
            try:
                validated_string = inputimeout(prompt="→ ", timeout=input_time)
            except TimeoutOccurred:
                return None
        except Exception as e:
            print(f"→ An error occurred: {e}")


# noinspection SpellCheckingInspection
def get_audio(video_id: str, folder: str, name: str) -> None:
    """Downloads audio from YouTube.

    Uses silent output.

    Uses FFmpeg in order to convert to mp3 file.
    """

    file_name = f"{folder}/{name}"
    file_name_mp3 = f"{file_name}.mp3"
    if os.path.isfile(file_name_mp3) and name.split("/")[-2] != "temp":
        if input(f"→ Would you like to overwrite {name.split("/")[-1]}? (Y/n) ") == "n":
            return
    try:
        os.remove(file_name_mp3)
    except FileNotFoundError:
        pass
    except WindowsError:
        pygame.mixer.quit()
        get_audio(video_id, folder, name)
    except Exception as e:
        print(f"→ An error occurred: {e}")

    # Downloads video from YouTube.
    try:
        video = YouTube(f"https://www.youtube.com/watch?v={video_id}")
        audio_stream = video.streams.filter(only_audio=True).first()
        if audio_stream:
            audio_stream.download(output_path="/".join(file_name.split("/")[:-1]),
                                  filename=f"{file_name.split("/")[-1]}.webm")
        else:
            print("Song not found.")
        # Converts audio to mp3 using FFmpeg.
        try:
            subprocess.run([
                "ffmpeg",
                "-i", f"{file_name}.webm",
                "-vn",
                "-acodec", "libmp3lame",
                "-q:a", "2",
                "-y",
                "-loglevel", "quiet",
                file_name_mp3
            ])
        except Exception as e:
            print(f"→ An error occurred: {e}")
        if os.path.isfile(file_name_mp3):
            try:
                os.remove(f"{file_name}.webm")
            except Exception as e:
                print(f"→ An error occurred: {e}")

        # Downloads audio thumbnail.
        urllib.request.urlretrieve(video.thumbnail_url, f"{file_name}.jpg")
        image = Image.open(f"{file_name}.jpg")
        width, height = image.size
        min_dim = min(width, height)
        crop_box = ((width - min_dim) // 2 + 60, (height - min_dim) // 2 + 60,
                    (width + min_dim) // 2 - 60, (height + min_dim) // 2 - 60)
        cropped_image = image.crop(crop_box)
        cropped_image.save(f"{file_name}.jpg")
        audiofile = eyed3.load(f"{file_name}.mp3")
        if audiofile.tag is None:
            audiofile.initTag()
        audiofile.tag.images.set(ImageFrame.FRONT_COVER, open(f"{file_name}.jpg", "rb")
                                 .read(), "image/jpeg")
        audiofile.tag.save(version=eyed3.id3.ID3_V2_3)
        os.remove(f"{file_name}.jpg")
    except pytubefix.exceptions.AgeRestrictedError:
        print("Cannot download this song!")
    except Exception as e:
        print(f"→ An error occurred: {e}")


def allow_pausing(current: str) -> None:
    """Prompts user for an input.

    User will now be able to pause currently playing music.

    Will call itself again in order to allow pausing

    if music is unpaused.
    """

    global current_audio
    global current_volume
    global past_position
    pausable = ""
    try:
        if pygame.mixer.music.get_pos() == -1:
            return
        audio = MP3(current)
        current_audio = audio

        # Checks if music is being streamed.
        path_list = current.split("/")
        if path_list[-1].replace(".mp3", "") == "file" and path_list[-2] == "temp":
            print("→ Now playing streamed music!")
        else:
            print(f"→ Now playing {path_list[-1].replace(".mp3", "")}!")

        # Allows for user input.
        pausable = inputimeout(prompt="→ ", timeout=audio.info.length
                               - pygame.mixer.music.get_pos() / 1000
                               - past_position)
    except TimeoutOccurred:
        pausable = "_"
    except Exception as e:
        print(f"→ An error occurred: {e}")

    # Checks if user intends to pause music, skip song,
    # select a new folder, change the volume or select a new song.
    try:
        if pausable == "/":
            pygame.mixer.music.pause()
            pausable = input("→ (Music paused!) ")
            if pausable:
                pygame.mixer.music.unpause()
                allow_pausing(current)
        elif pausable == "_":
            return
        elif pausable[0] == "%":
            try:
                pausable = float(pausable[1:]) / 100
                if 0 <= pausable <= 1:
                    pygame.mixer.music.set_volume(pausable)
                    current_volume = pausable
                else:
                    print("→ Volume must be set to a number between 0 and 100!")
                allow_pausing(current)
            except ValueError:
                print("→ Volume must be set to a number between 0 and 100!")
                allow_pausing(current)
            except Exception as e:
                print(f"→ An error occurred: {e}")
                main(input("→ "))
        elif pausable == "^":
            devices = tuple(pygame._sdl2.audio.get_audio_device_names(False))

            # Prompt user for intended audio device.
            for number, device in enumerate(devices):
                print(f"→ {number + 1}.", device)
            while True:
                input_number = validate_int()
                if len(devices) >= input_number >= 1:
                    break

            # Plays song with selected audio device.
            position = pygame.mixer.music.get_pos() / 1000 + past_position
            pygame.mixer.quit()
            try:
                pygame.mixer.init(devicename=devices[input_number - 1])
            except pygame.error:
                print("→ Cannot use this device!")
                allow_pausing(current)
            pygame.mixer.music.load(current)
            pygame.mixer.music.play()
            pygame.mixer.music.set_volume(current_volume)
            pygame.mixer.music.set_pos(position)
            past_position = position
            allow_pausing(current)
        else:
            main(pausable)
    except IndexError:
        main(pausable)
    except Exception as e:
        print(f"→ An error occurred: {e}")


def main(initial_input: str) -> None:
    """Handles initial user input.

    Takes user input and creates a list of songs.

    Downloads songs which are marked for downloading

    and uses local files otherwise.

    List of songs contains user specified order

    followed by a random assortment of local files.
    """

    global current_audio
    global current_volume
    global currently_playing
    global past_position
    global path
    input_time = 2147483647
    downloaded = False
    downloaded_name = ""
    titles = []

    try:
        # noinspection PyUnresolvedReferences
        input_time = (current_audio.info.length
                      - pygame.mixer.music.get_pos() / 1000
                      - past_position)
    except (AttributeError, pygame.error):
        pass
    except Exception as e:
        print(f"→ An error occurred: {e}")

    # Handles exiting the program, selecting a new music folder,
    # changing the volume, renaming a song and deleting a song.
    try:
        if initial_input == "\\":
            pygame.mixer.quit()
            try:
                shutil.rmtree(f"{path}/temp")
            except FileNotFoundError:
                pass
            except Exception as e:
                print(f"→ An error occurred: {e}")
            print("→ Exiting!")
            exit(0)
        elif initial_input == "_":
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                allow_pausing(currently_playing)
                return
            else:
                print("→ No music is playing!")
                main(input("→ "))
        elif initial_input == "#":
            get_path()
            try:
                main(inputimeout(prompt="→ ", timeout=input_time))
            except TimeoutOccurred:
                return
        elif initial_input[0] == "%":
            try:
                initial_input = float(initial_input[1:]) / 100
                if 0 <= initial_input <= 1:
                    pygame.mixer.music.set_volume(initial_input)
                    current_volume = initial_input
                else:
                    print("→ Volume must be set to a number between 0 and 100!")
                try:
                    main(inputimeout(prompt="→ ", timeout=input_time))
                except TimeoutOccurred:
                    return
            except ValueError:
                print("→ Volume must be set to a number between 0 and 100!")
                try:
                    main(inputimeout(prompt="→ ", timeout=input_time))
                except TimeoutOccurred:
                    return
            except pygame.error:
                pygame.mixer.init()
                # noinspection PyTypeChecker
                pygame.mixer.music.set_volume(initial_input)
                current_volume = initial_input
                try:
                    main(inputimeout(prompt="→ ", timeout=input_time))
                except TimeoutOccurred:
                    return
            except Exception as e:
                print(f"→ An error occurred: {e}")
                try:
                    main(inputimeout(prompt="→ ", timeout=input_time))
                except TimeoutOccurred:
                    return
        elif initial_input == "+":
            to_rename = input("→ ")
            rename = input("→ ")
            try:
                os.rename(f"{path}/{to_rename}.mp3", f"{path}/{rename}.mp3")
            except FileNotFoundError:
                try:
                    os.rename(f"{path}/{to_rename}", f"{path}/{rename}")
                except FileNotFoundError:
                    print("→ Does not exist!")
                except WindowsError:
                    print("→ Cannot rename!")
                except Exception as e:
                    print(f"→ An error occurred: {e}")
            except WindowsError:
                print("→ Cannot rename this song!")
            except Exception as e:
                print(f"→ An error occurred: {e}")
            try:
                main(inputimeout(prompt="→ ", timeout=input_time))
            except TimeoutOccurred:
                return
        elif initial_input == "=":
            remove = input("→ ")
            try:
                os.remove(f"{path}/{remove}.mp3")
            except FileNotFoundError:
                try:
                    shutil.rmtree(f"{path}/{remove}")
                except FileNotFoundError:
                    print("→ Does not exist!")
                except WindowsError:
                    print("→ Cannot delete!")
                except Exception as e:
                    print(f"→ An error occurred: {e}")
            except WindowsError:
                print("→ Cannot delete this song!")
            except Exception as e:
                print(f"→ An error occurred: {e}")
            try:
                main(inputimeout(prompt="→ ", timeout=input_time))
            except TimeoutOccurred:
                return
        elif initial_input == "^":
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            devices = tuple(pygame._sdl2.audio.get_audio_device_names(False))

            # Prompt user for intended audio device.
            for number, device in enumerate(devices):
                print(f"→ {number + 1}.", device)
            while True:
                input_number = validate_int()
                if len(devices) >= input_number >= 1:
                    break
            if pygame.mixer.music.get_busy():
                position = pygame.mixer.music.get_pos() / 1000 + past_position
                pygame.mixer.quit()
                try:
                    pygame.mixer.init(devicename=devices[input_number - 1])
                except pygame.error:
                    print("→ Cannot use this device!")
                    allow_pausing(currently_playing)
                pygame.mixer.music.load(currently_playing)
                pygame.mixer.music.play()

                # noinspection PyTypeChecker
                pygame.mixer.music.set_volume(current_volume)
                pygame.mixer.music.set_pos(position)
                past_position = position
            else:
                if pygame.mixer.get_init():
                    pygame.mixer.quit()
                try:
                    pygame.mixer.init(devicename=devices[input_number - 1])
                except pygame.error:
                    print("→ Cannot use this device!")
    except IndexError:
        pass
    except Exception as e:
        print(f"→ An error occurred: {e}")

    # Handles streaming a song from YouTube.
    try:
        if initial_input == initial_input.replace("_", ""):
            if initial_input == "-":
                try:
                    youtube_results = json.loads(YoutubeSearch(input("→ "),
                                                               max_results=10).to_json())
                    for number, video in enumerate(youtube_results["videos"]):
                        print(f"→ {number + 1}.", f"({video["channel"]}) {video["title"]}")
                    while True:
                        input_number = validate_int()
                        if 10 >= input_number >= 1:
                            break

                    # Downloads temporary audio file from YouTube.
                    get_audio(youtube_results["videos"][input_number - 1]["id"], path, "temp/file")
                    downloaded = True

                # Sends an error message and allows user to select a song
                # if streaming fails.
                except TypeError:
                    return
                except Exception as e:
                    logging.debug(e)
                    try:
                        downloaded = False
                        print("→ Cannot connect to server!")
                        try:
                            main(inputimeout(prompt="→ ", timeout=input_time))
                        except TimeoutOccurred:
                            return
                    except ValueError:
                        return
                    except Exception as e:
                        print(f"→ An error occurred: {e}")

            # Handles downloading a song from YouTube.
            elif initial_input == "'":
                try:
                    youtube_results = json.loads(YoutubeSearch(input("→ "),
                                                               max_results=10).to_json())
                    for number, video in enumerate(youtube_results["videos"]):
                        print(f"→ {number + 1}.", f"({video["channel"]}) {video["title"]}")
                    while True:
                        input_number = validate_int()
                        if 10 >= input_number >= 1:
                            break

                    # Gets song names from user.
                    title = clean(input("→ Please input a title for this song!\n→ "))
                    if os.path.isfile(f"{path}/{title}.mp3"):
                        if input(f"→ Would you like to overwrite {title}? (Y/n) ") == "n":
                            try:
                                main(inputimeout(prompt="→ ", timeout=input_time))
                            except TimeoutOccurred:
                                return
                        else:
                            os.remove(f"{path}/{title}.mp3")

                    # Downloads audio file from YouTube.
                    get_audio(youtube_results["videos"][input_number - 1]["id"], path, title)
                    downloaded_name = f"{title}.mp3"

                # Sends an error message and allows user to select a song
                # if downloading fails.
                except TypeError:
                    return
                except Exception as e:
                    logging.debug(e)
                    try:
                        downloaded = False
                        print("→ Cannot connect to server!")
                        try:
                            main(inputimeout(prompt="→ ", timeout=input_time))
                        except TimeoutOccurred:
                            return
                    except ValueError:
                        return
                    except Exception as e:
                        print(f"→ An error occurred: {e}")

            # Handles streaming an album from YouTube.
            elif initial_input == "$":
                playlist_url = input("→ ")
                try:
                    playlist = Playlist(playlist_url)
                    titles = [f"temp/{clean(YouTube(url).title)}" for url in playlist.video_urls]

                    # Downloads audio files from YouTube.
                    for number, url in enumerate(playlist.video_urls):
                        song_name = titles[number]
                        print(f"→ Now downloading {song_name.split("temp/")[1]}! ")
                        get_audio(str(url).split("v=")[1], path, song_name)

                # Sends an error message and allows user to select a song
                # if downloading fails.
                except TypeError:
                    return
                except Exception as e:
                    logging.debug(e)
                    try:
                        downloaded = False
                        print("→ Cannot connect to server!")
                        try:
                            main(inputimeout(prompt="→ ", timeout=input_time))
                        except TimeoutOccurred:
                            return
                    except ValueError:
                        return
                    except Exception as e:
                        print(f"→ An error occurred: {e}")

            # Handles downloading an album from YouTube.
            elif initial_input == '"':
                playlist_url = input("→ ")
                try:
                    playlist = Playlist(playlist_url)
                    selected_titles = []
                    youtube_titles = [YouTube(url).title for url in playlist.video_urls]

                    # Gets song names from user.
                    playlist_path = input(f"→ Please input a title for {playlist.title}!\n→ ")
                    while playlist_path == "temp":
                        playlist_path = input(f"→ Please input a title for {playlist.title}!\n→ ")
                    for youtube_title in youtube_titles:
                        selected_title = input(f"→ Please input a title for {youtube_title}!\n→ ")
                        if selected_title == "-":
                            try:
                                main(inputimeout(prompt="→ ", timeout=input_time))
                            except TimeoutOccurred:
                                return
                            return
                        selected_titles.append(f"{clean(playlist_path)}/{clean(selected_title)}")

                    # Downloads audio files from YouTube.
                    for number, url in enumerate(playlist.video_urls):
                        song_name = selected_titles[number]
                        print(f"→ Now downloading {song_name.split("/")[-1]}! ")
                        get_audio(str(url).split("v=")[1], path, song_name)

                    # Allows user to select a song to play.
                    try:
                        main(inputimeout(prompt="→ ", timeout=input_time))
                    except TimeoutOccurred:
                        return

                # Sends an error message and allows user to select a song
                # if downloading fails.
                except TypeError:
                    return
                except Exception as e:
                    logging.debug(e)
                    try:
                        downloaded = False
                        print("→ Cannot connect to server!")
                        try:
                            main(inputimeout(prompt="→ ", timeout=input_time))
                        except TimeoutOccurred:
                            return
                    except ValueError:
                        return
                    except Exception as e:
                        print(f"→ An error occurred: {e}")

            # Handles playing an album.
            elif initial_input == ":":
                albums = []
                intended_albums = []

                # Gets all albums in folder.
                for root, dirs, files in os.walk(path):
                    album_name = os.path.split(root)[-1]
                    if album_name != "temp" and files and not dirs:
                        albums.append(album_name)
                if not albums:
                    print("→ No albums found!")

                # Finds characters to match to user input.
                else:
                    initial_input = input("→ ")
                    input_characters = list((initial_input.split(" "))[0])
                    for album in albums:
                        album_words = album.split(" ")
                        if len(album_words) > 1:
                            album_characters = []
                            for word in album_words:
                                try:
                                    album_characters.append(((list(word))[0]).lower())
                                except IndexError:
                                    pass
                                except Exception as e:
                                    print(f"→ An error occurred: {e}")
                        else:
                            album_characters = [character.lower() for character in list(album)]

                        # Checks if user input matches album.
                        counter = 0
                        for letter in list(input_characters):
                            if letter in album_characters:
                                counter += 1
                        if counter == len(list(input_characters)):
                            intended_albums.append(album)

                    # Prompts user for which album to play
                    # if multiple albums match user input.
                    if intended_albums:
                        if len(intended_albums) > 1:
                            no_index = False
                            try:
                                int((initial_input.split(" "))[1])
                            except (IndexError, ValueError):
                                no_index = True
                            except Exception as e:
                                print(f"→ An error occurred: {e}")
                            if (len(initial_input.split(" ")) == 1) or no_index:
                                for number, playable_album in enumerate(intended_albums):
                                    print(f"→ {number + 1}.", playable_album)
                                index = validate_int()

                            # Accounts for if user has already selected
                            # which album to play
                            # if multiple albums match input.
                            else:
                                index = int((initial_input.split(" "))[1])
                        else:
                            index = 0
                    else:
                        print("→ No albums found!")
                        try:
                            main(inputimeout(prompt="→ ", timeout=input_time))
                        except TimeoutOccurred:
                            return
                        return

                    # noinspection PyUnboundLocalVariable
                    album_path = intended_albums[index - 1]
                    album_songs = [song for song in os.listdir(f"{path}/{album_path}")
                                   if song[-4:] == ".mp3"]
                    album_songs.sort(key=lambda x: os.path.getmtime(f"{path}/{album_path}/{x}"))
                    pygame.mixer.init()

                    # Plays all songs in selected album.
                    for playable_song in album_songs:
                        currently_playing = f"{path}/{album_path}/{playable_song}"
                        try:
                            pygame.mixer.music.load(currently_playing)
                        except pygame.error:
                            return
                        except Exception as e:
                            print(f"→ An error occurred: {e}")
                        past_position = 0
                        pygame.mixer.music.play()
                        allow_pausing(currently_playing)
                try:
                    main(inputimeout(prompt="→ ", timeout=input_time))
                except TimeoutOccurred:
                    return

            # Creates variables for creating list of songs to be played.
            all_songs = []
            intended_songs = []
            intended_song_paths = []
            input_characters = list((initial_input.split(" "))[0])

            # Finds characters to match to user input.
            for song, song_path in get_songs(path):
                all_songs.append(song)
                song_words = song.split(" ")
                if len(song_words) > 1:
                    song_characters = []
                    for word in song_words:
                        try:
                            song_characters.append(((list(word))[0]).lower())
                        except IndexError:
                            pass
                        except Exception as e:
                            print(f"→ An error occurred: {e}")
                else:
                    song_characters = list((song.split(".mp3"))[0])
                song_characters = [character.lower() for character in song_characters]

                # Checks if user input matches song.
                counter = 0
                for letter in list(input_characters):
                    if letter in song_characters:
                        counter += 1
                if counter == len(list(input_characters)) and song_path != "temp/":
                    intended_songs.append(song)
                    intended_song_paths.append(song_path)
            if not downloaded:
                intended_songs = [song_path for number, song_path
                                  in enumerate(intended_songs)
                                  if os.path.isfile(f"{path}/{intended_song_paths[number]}"
                                                    f"{song_path}")]
            else:
                intended_songs = [""]

            # Prompts user for which song to play
            # if multiple songs match user input.
            if intended_songs:
                if len(intended_songs) > 1:
                    if (not downloaded) and (downloaded_name == ""):
                        no_index = False
                        try:
                            int((initial_input.split(" "))[1])
                        except (IndexError, ValueError):
                            no_index = True
                        except Exception as e:
                            print(f"→ An error occurred: {e}")
                        if (len(initial_input.split(" ")) == 1) or no_index:
                            for number, playable_song in enumerate(intended_songs):
                                if intended_song_paths[number] != "":
                                    intended_path = f"({intended_song_paths[number]
                                                        .replace("/", "")}) "
                                else:
                                    intended_path = ""
                                print(f"→ {number + 1}. {intended_path}{playable_song[:-4]}")
                            index = validate_int()

                        # Accounts for if user has already selected
                        # which song to play if multiple songs match input.
                        else:
                            index = int((initial_input.split(" "))[1])

                    # Initializes music player
                    # and creates list of songs to be played.
                    pygame.mixer.init()
                    all_songs = [f"{song_path}{song}" for song, song_path in get_songs(path)
                                 if song_path.split("/")[0] != "temp"]

                    # Adds streamed and downloaded songs
                    # to list of songs to be played.
                    if downloaded_name != "":
                        random.shuffle(all_songs)
                        all_songs.insert(0, downloaded_name)
                    elif not downloaded:
                        try:
                            random.shuffle(all_songs)

                            # noinspection PyUnboundLocalVariable
                            specific_song = intended_songs[index - 1]
                            specific_song_path = intended_song_paths[index - 1]
                            try:
                                all_songs.remove(f"{specific_song_path}{specific_song}")
                            except ValueError:
                                pass
                            all_songs.insert(0, f"{specific_song_path}{specific_song}")
                        except IndexError:
                            print("→ This song cannot be played!")
                            try:
                                main(inputimeout(prompt="→ ", timeout=input_time))
                            except TimeoutOccurred:
                                return
                        except TypeError:
                            return
                        except Exception as e:
                            print(f"→ An error occurred: {e}")
                    else:
                        random.shuffle(all_songs)
                        all_songs.insert(0, "temp/file.mp3")
                        print(all_songs)

                    # Plays songs in list of songs to be played.
                    for playable_song in all_songs:
                        currently_playing = f"{path}/{playable_song}"
                        try:
                            pygame.mixer.music.load(currently_playing)
                        except pygame.error:
                            return
                        except Exception as e:
                            print(f"→ An error occurred: {e}")
                        past_position = 0
                        pygame.mixer.music.play()

                        # Allows user to pause music.
                        if downloaded_name != "":
                            allow_pausing(f"{path}/{downloaded_name}")
                            downloaded_name = ""
                        elif downloaded:
                            allow_pausing(currently_playing)
                        else:
                            allow_pausing(currently_playing)
                    get_path()
                    try:
                        main(inputimeout(prompt="→ ", timeout=input_time))
                    except TimeoutOccurred:
                        return

                # Initializes music player
                # and creates list of songs to be played.
                else:
                    pygame.mixer.init()
                    all_songs = [f"{song_path}{song}" for song, song_path in get_songs(path)
                                 if song_path.split("/")[0] != "temp"]
                    random.shuffle(all_songs)

                    # Adds streamed and downloaded songs
                    # to list of songs to be played.
                    if downloaded_name != "":
                        all_songs.insert(0, downloaded_name)
                    elif not downloaded:
                        try:
                            all_songs.remove(f"{intended_song_paths[0]}{intended_songs[0]}")
                        except ValueError:
                            pass
                        except Exception as e:
                            print(f"→ An error occurred: {e}")
                        all_songs.insert(0, f"{intended_song_paths[0]}{intended_songs[0]}")
                    else:
                        all_songs.insert(0, "temp/file.mp3")

                    # Plays songs in list of songs to be played.
                    for playable_song in all_songs:
                        currently_playing = f"{path}/{playable_song}"
                        try:
                            pygame.mixer.music.load(currently_playing)
                        except pygame.error:
                            return
                        except Exception as e:
                            print(f"→ An error occurred: {e}")
                        past_position = 0
                        pygame.mixer.music.play()

                        # Allows user to pause music.
                        if downloaded_name != "":
                            allow_pausing(f"{path}/{downloaded_name}")
                            downloaded_name = ""
                        elif downloaded:
                            allow_pausing(currently_playing)
                        else:
                            allow_pausing(currently_playing)
                    get_path()
                    try:
                        main(inputimeout(prompt="→ ", timeout=input_time))
                    except TimeoutOccurred:
                        return
            elif titles:
                random.shuffle(all_songs)
                titles = titles[::-1]
                for title in titles:
                    all_songs.insert(0, f"{title}.mp3")
                pygame.mixer.init()
                for playable_song in all_songs:
                    currently_playing = f"{path}/{playable_song}"
                    try:
                        pygame.mixer.music.load(currently_playing)
                    except pygame.error:
                        return
                    except Exception as e:
                        print(f"→ An error occurred: {e}")
                    past_position = 0
                    pygame.mixer.music.play()
                    allow_pausing(currently_playing)
                get_path()
                try:
                    main(inputimeout(prompt="→ ", timeout=input_time))
                except TimeoutOccurred:
                    return

            # Allows user to select music to play if none is found.
            if (initial_input != "-") and (initial_input != "'"):
                print("→ No music found!")
            try:
                main(inputimeout(prompt="→ ", timeout=input_time))
            except TimeoutOccurred:
                return

        # Creates shuffled list of music to be played.
        else:
            all_songs = [f"{song_path}{song}" for song, song_path in get_songs(path)
                         if song_path.split("/")[0] != "temp"]
            random.shuffle(all_songs)

            # Handles each song in user input separately.
            counter = 0
            for song in initial_input.split("_"):
                intended_songs = []
                intended_song_paths = []
                for individual_input in song.split("_"):
                    input_characters = list((individual_input.split(" "))[0])
                    if not input_characters:
                        print("→ Cannot play this song!\n→ ")
                        try:
                            main(inputimeout(prompt="→ ", timeout=input_time))
                        except TimeoutOccurred:
                            return
                    elif input_characters[0] != "-":
                        for inputs, song_path in get_songs(path):
                            song_words = inputs.split(" ")
                            if len(song_words) > 1:
                                song_characters = []
                                for word in song_words:
                                    try:
                                        song_characters.append(((list(word))[0]).lower())
                                    except IndexError:
                                        pass
                                    except Exception as e:
                                        print(f"→ An error occurred: {e}")
                            else:
                                song_characters = list((inputs.split(".mp3"))[0])
                            song_characters = [character.lower() for character in song_characters]
                            matching_characters = 0
                            for letter in list(input_characters):
                                if letter in song_characters:
                                    matching_characters += 1

                            # Adds song to list of songs to be played
                            # if it matches user input.
                            if matching_characters == len(list(input_characters)):
                                intended_songs.append(inputs)
                                intended_song_paths.append(song_path)
                            intended_songs = [song_path for number, song_path
                                              in enumerate(intended_songs)
                                              if os.path.isfile(f"{path}"
                                                                f"/{intended_song_paths[number]}"
                                                                f"{song_path}")]

                        # Prompts user for which song to play
                        # if multiple songs match user input.
                        if intended_songs:
                            if len(intended_songs) > 1:
                                no_index = False
                                try:
                                    int((individual_input.split(" "))[1])
                                except (IndexError, ValueError):
                                    no_index = True
                                except Exception as e:
                                    print(f"→ An error occurred: {e}")
                                if no_index:
                                    intended_songs = [song for number, song
                                                      in enumerate(intended_songs)
                                                      if intended_song_paths[number]
                                                      .replace("/", "")
                                                      != "temp"]
                                    for number, playable_song in enumerate(intended_songs):
                                        if intended_song_paths[number] != "":
                                            intended_path = f"({intended_song_paths[number]
                                                                .replace("/", "")}) "
                                        else:
                                            intended_path = ""
                                        print(f"→ {number + 1}. "
                                              f"{intended_path}{playable_song[:-4]}")
                                    index = validate_int()

                                # Accounts for if user has already
                                # selected which song to play
                                # if multiple songs match input.
                                else:
                                    index = int((individual_input.split(" "))[1])

                                # Moves song to be played to front
                                # of list of songs to be played.
                                try:
                                    specific_song = intended_songs[index - 1]
                                    specific_song_path = intended_song_paths[index - 1]
                                    try:
                                        all_songs.remove(f"{specific_song_path}{specific_song}")
                                    except ValueError:
                                        pass
                                    except Exception as e:
                                        print(f"→ An error occurred: {e}")
                                    all_songs.insert(counter,
                                                     f"{specific_song_path}{specific_song}")
                                except IndexError:
                                    print("→ This song cannot be played!")
                                    try:
                                        main(inputimeout(prompt="→ ", timeout=input_time))
                                    except TimeoutOccurred:
                                        return
                                except Exception as e:
                                    print(f"→ An error occurred: {e}")
                            elif intended_song_paths[0].replace("/", "") != "temp":
                                specific_song = intended_songs[0]
                                specific_song_path = intended_song_paths[0]
                                try:
                                    all_songs.remove(f"{specific_song_path}{specific_song}")
                                except ValueError:
                                    pass
                                except Exception as e:
                                    print(f"→ An error occurred: {e}")
                                all_songs.insert(counter, f"{specific_song_path}{specific_song}")
                    else:
                        try:
                            youtube_results = json.loads(YoutubeSearch(
                                individual_input.replace("-", ""), max_results=1).to_json())
                            name = youtube_results["videos"][0]["title"]
                            print(f"→ Now downloading {name}! ")
                            title = f"temp/{clean(name)}"
                            get_audio(youtube_results["videos"][0]["id"], path, title)
                            all_songs.insert(counter, f"{title}.mp3")

                        # Sends an error message and allows user
                        # to select a song if downloading fails.
                        except Exception as e:
                            print("→ Cannot connect to server!")
                            logging.debug(e)
                            try:
                                main(inputimeout(prompt="→ ", timeout=input_time))
                            except TimeoutOccurred:
                                return

                # Moves onto next position in list of songs to be played.
                counter += 1

            # Removes temp folder from list of songs to be played.
            pygame.mixer.init()
            all_songs = [song_path for song_path in all_songs
                         if os.path.isfile(f"{path}/{song_path}")]

            # Plays songs in list of songs to be played.
            for playable_song in all_songs:
                currently_playing = f"{path}/{playable_song}"
                try:
                    pygame.mixer.music.load(currently_playing)
                except pygame.error:
                    pass
                except Exception as e:
                    print(f"→ An error occurred: {e}")
                past_position = 0
                pygame.mixer.music.play()
                allow_pausing(currently_playing)
            get_path()
            try:
                main(inputimeout(prompt="→ ", timeout=input_time))
            except TimeoutOccurred:
                return
    except AttributeError:
        return
    except Exception as e:
        print(f"→ An error occurred: {e}")


# Prompts user for music folder before allowing user to select songs.
if __name__ == "__main__":
    get_path()
    main(input("→ "))
