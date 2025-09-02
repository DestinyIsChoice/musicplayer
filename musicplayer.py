import json
import logging
import os
import random
import shutil
import sys

from inputimeout import inputimeout, TimeoutOccurred
from mutagen.mp3 import MP3
import pygame
from pytubefix import YouTube, Playlist
from youtube_search import YoutubeSearch
import yt_dlp as youtube_dl

# noinspection SpellCheckingInspection
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
path = ""


def clean(string: str) -> str:
    """Removes illegal characters from a string used as a file name."""

    return string.translate(str.maketrans('', '', '"/\\<>*:|?'))


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
        if os.path.isdir(path):
            if not os.listdir(path):
                print("→ This folder currently contains no music! ")
            return
        else:
            if input("→ Would you like to create a new folder? (Y/n) ") == "n":
                get_path()
                return
            else:
                try:
                    os.mkdir(path)
                except OSError:
                    get_path()
                except Exception as e:
                    print(f"An error occurred: {e}")
                return


def validate_int() -> int | None:
    """Validates a user input as an integer.

    Will prompt user for a new input

    if previous could not be transformed into an integer.
    """

    # Validates input as an integer by having user input again
    # if not transformable to integer.
    validated_string = input("→ ")
    while True:

        # Allows user to select a song if selecting is cancelled.
        if validated_string == "-":
            main(input("→ "))
            return None

        # Validates user input as integer
        else:
            try:
                validated_string = int(validated_string)
                return validated_string
            except ValueError:
                validated_string = input("→ ")
            except Exception as e:
                print(f"An error occurred: {e}")


# noinspection SpellCheckingInspection
def get_audio(video_id: str, folder: str, name: str) -> None:
    """Downloads audio from YouTube.

    Uses silent output.

    Uses ffmpeg to get mp3 file.
    """

    filename = f"{folder}/{name}.mp3"
    if os.path.isfile(filename) and name.split("/")[0] != "temp":
        if input(f"→ Would you like to overwrite {name.split("/")[-1]}? (Y/n) ") == "n":
            return
    try:
        os.remove(filename)
    except FileNotFoundError:
        pass
    except WindowsError:
        pygame.mixer.quit()
        get_audio(video_id, folder, name)
    except Exception as e:
        print(f"An error occurred: {e}")

    # Silences output by redirecting stdout to nothing.
    old_stdout = sys.stdout
    sys.stdout = open(os.devnull, "w")

    # Downloads audio from YouTube as mp3 using ffmpeg.
    with youtube_dl.YoutubeDL({
        'no_warnings': True,
        'format': 'bestaudio/best',
        'outtmpl': f"{folder}/{name}",
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'
        }]
    }) as ydl:
        ydl.download([f"https://www.youtube.com/watch?v={video_id}"])

    # Redirects stdout back to command line.
    sys.stdout = old_stdout


def allow_pausing(current: str) -> None:
    """Prompts user for an input.

    User will now be able to pause currently playing music.

    Will call itself again in order to allow pausing

    if music is unpaused.
    """

    pausable = ""
    try:
        audio = MP3(current)

        # Checks if music is being streamed.
        if (((current.split("/"))[(len(current.split("/"))) - 1]).replace(".mp3", "")) == "file":
            print("→ Now playing streamed music!")
        else:
            print(f"→ Now playing {((current.split("/"))[(len(current.split("/"))) - 1])
                  .replace(".mp3", "")}!")

        # Allows for user input.
        pausable = inputimeout(
            prompt="→ ", timeout=(audio.info.length - (pygame.mixer.music.get_pos() / 1000)))
    except TimeoutOccurred:
        pausable = "_"
    except Exception as e:
        print(f"An error occurred: {e}")

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
                else:
                    print("→ Volume must be set to a number between 0 and 100!")
                allow_pausing(current)
            except ValueError:
                print("→ Volume must be set to a number between 0 and 100!")
                allow_pausing(current)
            except Exception as e:
                print(f"An error occurred: {e}")
                main(input("→ "))
        else:
            main(pausable)
    except IndexError:
        main(pausable)
    except Exception as e:
        print(f"An error occurred: {e}")


def main(initial_input: str) -> None:
    """Handles initial user input.

    Takes user input and creates a list of songs.

    Downloads songs which are marked for downloading

    and uses local files otherwise.

    List of songs contains user specified order

    followed by a random assortment of local files.
    """

    global path
    downloaded = False
    downloaded_name = ""
    titles = []

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
                print(f"An error occurred: {e}")
            print("→ Exiting!")
            exit(0)
        elif initial_input == "_":
            main(input("→ "))
        elif initial_input == "#":
            get_path()
            main(input("→ "))
        elif initial_input[0] == "%":
            try:
                initial_input = float(initial_input[1:]) / 100
                if 0 <= initial_input <= 1:
                    pygame.mixer.music.set_volume(initial_input)
                else:
                    print("→ Volume must be set to a number between 0 and 100!")
                main(input("→ "))
            except ValueError:
                print("→ Volume must be set to a number between 0 and 100!")
                main(input("→ "))
            except pygame.error:
                pygame.mixer.init()
                pygame.mixer.music.set_volume(initial_input)
                main(input("→ "))
            except Exception as e:
                print(f"An error occurred: {e}")
                main(input("→ "))
        elif initial_input == "+":
            try:
                os.rename(f"{path}/{input("→ ")}.mp3", f"{path}/{input("→ ")}.mp3")
            except FileNotFoundError:
                print("→ This song does not exist!")
            except WindowsError:
                print("→ Cannot rename this song!")
            except Exception as e:
                print(f"An error occurred: {e}")
            main(input("→ "))
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
                    print(f"An error occurred: {e}")
            except WindowsError:
                print("→ Cannot delete this song!")
            except Exception as e:
                print(f"An error occurred: {e}")
            main(input("→ "))
    except IndexError:
        pass
    except Exception as e:
        print(f"An error occurred: {e}")

    # Handles streaming a song from YouTube.
    if initial_input == initial_input.replace("_", ""):
        if initial_input == "-":
            try:
                youtube_results = json.loads(YoutubeSearch(input("→ "), max_results=10).to_json())
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
            except Exception as e:
                logging.debug(e)
                try:
                    downloaded = False
                    print("→ Cannot connect to server!")
                    main(input("→ "))
                except ValueError:
                    return
                except Exception as e:
                    print(f"An error occurred: {e}")

        # Handles downloading a song from YouTube.
        elif initial_input == "'":
            try:
                youtube_results = json.loads(YoutubeSearch(input("→ "), max_results=10).to_json())
                for number, video in enumerate(youtube_results["videos"]):
                    print(f"→ {number + 1}.", f"({video["channel"]}) {video["title"]}")
                while True:
                    input_number = validate_int()
                    if 10 >= input_number >= 1:
                        break

                # Gets song names from user.
                title = clean(input("→ Please input a title for this song!\n→ "))

                # Downloads audio file from YouTube.
                get_audio(youtube_results["videos"][input_number - 1]["id"], path, title)
                downloaded_name = f"{title}.mp3"

            # Sends an error message and allows user to select a song
            # if downloading fails.
            except Exception as e:
                logging.debug(e)
                try:
                    downloaded = False
                    print("→ Cannot connect to server!")
                    main(input("→ "))
                except ValueError:
                    return
                except Exception as e:
                    print(f"An error occurred: {e}")

        # Handles streaming a playlist from YouTube.
        elif initial_input == "$":
            playlist_url = input("→ ")
            try:
                playlist = Playlist(playlist_url)
                titles = []
                titles = [f"temp/{clean(YouTube(url).title)}" for url in playlist.video_urls]

                # Downloads audio files from YouTube.
                for number, url in enumerate(playlist.video_urls):
                    song_name = titles[number]
                    print(f"→ Now downloading {song_name.split("temp/")[1]}! ")
                    get_audio(str(url).split("v=")[1], path, song_name)

            # Sends an error message and allows user to select a song
            # if downloading fails.
            except Exception as e:
                logging.debug(e)
                try:
                    downloaded = False
                    print("→ Cannot connect to server!")
                    main(input("→ "))
                except ValueError:
                    return
                except Exception as e:
                    print(f"An error occurred: {e}")

        # Handles downloading a playlist from YouTube.
        elif initial_input == '"':
            playlist_url = input("→ ")
            try:
                playlist = Playlist(playlist_url)
                selected_titles = []
                youtube_titles = [YouTube(url).title for url in playlist.video_urls]

                # Gets song names from user.
                playlist_path = input(f"→ Please input a title for {playlist.title}!\n→ ")
                for youtube_title in youtube_titles:
                    selected_title = input(f"→ Please input a title for {youtube_title}!\n→ ")
                    if selected_title == "-":
                        main(input("→ "))
                        return
                    selected_titles.append(f"{clean(playlist_path)}/{clean(selected_title)}")

                # Downloads audio files from YouTube.
                for number, url in enumerate(playlist.video_urls):
                    song_name = selected_titles[number]
                    print(f"→ Now downloading {song_name.split("/")[-1]}! ")
                    get_audio(str(url).split("v=")[1], path, song_name)

                # Allows user to select a song to play.
                main(input("→ "))

            # Sends an error message and allows user to select a song
            # if downloading fails.
            except Exception as e:
                logging.debug(e)
                try:
                    downloaded = False
                    print("→ Cannot connect to server!")
                    main(input("→ "))
                except ValueError:
                    return
                except Exception as e:
                    print(f"An error occurred: {e}")

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
                        album_characters = [((list(word))[0]).lower() for word in album_words]
                    else:
                        album_characters = [character.lower() for character in list(album)]

                    # Checks if user input matches song.
                    counter = 0
                    for letter in list(input_characters):
                        if letter in album_characters:
                            counter += 1
                    if counter == len(list(input_characters)):
                        intended_albums.append(album)

                # Prompts user for which song to play
                # if multiple songs match user input.
                if intended_albums:
                    if len(intended_albums) > 1:
                        no_index = False
                        try:
                            int((initial_input.split(" "))[1])
                        except (IndexError, ValueError):
                            no_index = True
                        except Exception as e:
                            print(f"An error occurred: {e}")
                        if (len(initial_input.split(" ")) == 1) or no_index:
                            for number, playable_album in enumerate(intended_albums):
                                print(f"→ {number + 1}.", playable_album)
                            index = validate_int()

                        # Accounts for if user has already selected
                        # which song to play
                        # if multiple songs match input.
                        else:
                            index = int((initial_input.split(" "))[1])
                    else:
                        index = 0
                else:
                    print("→ No albums found!")
                    main(input("→ "))
                    return

                # noinspection PyUnboundLocalVariable
                album_path = intended_albums[index - 1]
                album_songs = [song for song in os.listdir(f"{path}/{album_path}")
                               if song[-4:] == ".mp3"]
                album_songs.sort(key=lambda x: os.path.getmtime(f"{path}/{album_path}/{x}"))
                pygame.mixer.init()

                # Plays all songs in selected album.
                for playable_song in album_songs:
                    try:
                        pygame.mixer.music.load(f"{path}/{album_path}/{playable_song}")
                    except pygame.error:
                        return
                    except Exception as e:
                        print(f"An error occurred: {e}")
                    pygame.mixer.music.play()
                    allow_pausing(f"{path}/{album_path}/{playable_song}")
            main(input("→ "))

        # Creates variables for creating list of songs to be played.
        all_songs = []
        intended_songs = [""] if downloaded else []
        input_characters = list((initial_input.split(" "))[0])

        # Finds characters to match to user input.
        for song in os.listdir(path):
            all_songs.append(song)
            song_words = song.split(" ")
            if len(song_words) > 1:
                song_characters = [((list(word))[0]).lower() for word in song_words]
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
        intended_songs = [song_path for song_path in intended_songs
                          if os.path.isfile(f"{path}/{song_path}")]

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
                        print(f"An error occurred: {e}")
                    if (len(initial_input.split(" ")) == 1) or no_index:
                        for number, playable_song in enumerate(intended_songs):
                            print(f"→ {number + 1}.", playable_song[:-4])
                        index = validate_int()

                    # Accounts for if user has already selected
                    # which song to play if multiple songs match input.
                    else:
                        index = int((initial_input.split(" "))[1])

                # Initializes music player
                # and creates list of songs to be played.
                pygame.mixer.init()
                all_songs = [song_path for song_path in all_songs
                             if os.path.isfile(f"{path}/{song_path}")]

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
                        all_songs.remove(specific_song)
                        all_songs.insert(0, specific_song)
                    except IndexError:
                        print("→ This song cannot be played!")
                        main(input("→ "))
                    except Exception as e:
                        print(f"An error occurred: {e}")
                else:
                    random.shuffle(all_songs)
                    all_songs.insert(0, "temp/file.mp3")

                # Plays songs in list of songs to be played.
                for playable_song in all_songs:
                    try:
                        pygame.mixer.music.load(f"{path}/{playable_song}")
                    except pygame.error:
                        return
                    except Exception as e:
                        print(f"An error occurred: {e}")
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

            # Initializes music player
            # and creates list of songs to be played.
            else:
                pygame.mixer.init()
                all_songs = [song_path for song_path in all_songs
                             if os.path.isfile(f"{path}/{song_path}")]
                random.shuffle(all_songs)

                # Adds streamed and downloaded songs
                # to list of songs to be played.
                if downloaded_name != "":
                    all_songs.insert(0, downloaded_name)
                elif not downloaded:
                    all_songs.remove(intended_songs[0])
                    all_songs.insert(0, intended_songs[0])
                else:
                    all_songs.insert(0, "temp/file.mp3")

                # Plays songs in list of songs to be played.
                for playable_song in all_songs:
                    try:
                        pygame.mixer.music.load(f"{path}/{playable_song}")
                    except pygame.error:
                        return
                    except Exception as e:
                        print(f"An error occurred: {e}")
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
        elif titles:
            random.shuffle(all_songs)
            titles = titles[::-1]
            for title in titles:
                all_songs.insert(0, f"{title}.mp3")
            pygame.mixer.init()
            for playable_song in all_songs:
                try:
                    pygame.mixer.music.load(f"{path}/{playable_song}")
                except pygame.error:
                    return
                except Exception as e:
                    print(f"An error occurred: {e}")
                pygame.mixer.music.play()
                allow_pausing(f"{path}/{playable_song}")
            get_path()
            main(input("→ "))

        # Allows user to select music to play if none is found.
        if (initial_input != "-") and (initial_input != "'"):
            print("→ No music found!")
        main(input("→ "))

    # Creates shuffled list of music to be played.
    else:
        all_songs = [song for song in os.listdir(path)]
        random.shuffle(all_songs)

        # Handles each song in user input separately.
        counter = 0
        for song in initial_input.split("_"):
            intended_songs = []
            for individual_input in song.split("_"):
                input_characters = list((individual_input.split(" "))[0])
                if not input_characters:
                    print("→ Cannot play this song!\n→ ")
                    main(input("→ "))
                elif input_characters[0] != "-":
                    for inputs in os.listdir(path):
                        song_words = inputs.split(" ")
                        if len(song_words) > 1:
                            song_characters = [((list(word))[0]).lower() for word in song_words]
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
                        intended_songs = [song_path for song_path in intended_songs
                                          if os.path.isfile(f"{path}/{song_path}")]

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
                                print(f"An error occurred: {e}")
                            if no_index:
                                for number, playable_song in enumerate(intended_songs):
                                    print(f"→ {number + 1}.", playable_song[:-4])
                                index = validate_int()

                            # Accounts for if user has already
                            # selected which song to play
                            # if multiple songs match input.
                            else:
                                index = int((individual_input.split(" "))[1])

                            # Moves song to be played to front
                            # of list of songs to be played.
                            specific_song = intended_songs[index - 1]
                            all_songs.remove(specific_song)
                            all_songs.insert(counter, specific_song)
                        else:
                            specific_song = intended_songs[0]
                            all_songs.remove(specific_song)
                            all_songs.insert(counter, specific_song)
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
                        main(input("→ "))

            # Moves onto next position in list of songs to be played.
            counter += 1

        # Removes temp folder from list of songs to be played.
        pygame.mixer.init()
        all_songs = [song_path for song_path in all_songs if os.path.isfile(f"{path}/{song_path}")]

        # Plays songs in list of songs to be played.
        for playable_song in all_songs:
            try:
                pygame.mixer.music.load(f"{path}/{playable_song}")
            except pygame.error:
                return
            except Exception as e:
                print(f"An error occurred: {e}")
            pygame.mixer.music.play()
            allow_pausing(f"{path}/{playable_song}")
        get_path()
        main(input("→ "))


# Prompts user for music folder before allowing user to select songs.
if __name__ == "__main__":
    get_path()
    main(input("→ "))
