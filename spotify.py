"""
Step 1: Login into youtube
Step 2: Grab your liked vids
Step 3: Create a new playlist in Spotify
Step 4: Search for the song
Step 5: Add this song to the spotify playlist
"""

import json
import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import requests
import youtube_dl
# from exceptions import ResponseException
from secrets import spotify_token, spotify_user_id


class CreatePlaylist:

    def __init__(self):
        self.user_id = spotify_user_id
        self.spotify_token = spotify_token
        self.youtube_client = self.get_youtube_client()
        self.all_song_info = {}

# Step 1: Login into youtube
    def get_youtube_client(self):
        # copied from Youtube Data API
        """ Log Into Youtube, Copied from Youtube Data API """
        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "client_secret.json"

        # Get credentials and create an API client
        scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        credentials = flow.run_console()

        # from the Youtube DATA API
        youtube_client = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)

        return youtube_client

# Step 2: Grab your liked vids
    def get_liked_videos(self):
        request = self.youtube_client.videos().list(
            part="snippet, contentDetails, statistics",
            maxResults=10,
            myRating="like"
        )
        response = request.execute()
        # collect each video and get important information
        for item in response["items"]:
            video_title = item["snippet"]["title"]
            youtube_url = "https://www.youtube.com/watch?v={}".format(item["id"])

            # use youtube_dl to collect the song name & artist name
            video = youtube_dl.YoutubeDL({}).extract_info(
                youtube_url, download=False)
            song_name = video["track"]
            artist = video["artist"]
            print(song_name)
            print(artist)

#            if self.get_spotify_uri()
            if song_name is not None and artist is not None:
                spotify_uri = self.get_spotify_uri(song_name, artist)
                if spotify_uri is not None:
                    self.all_song_info[video_title] = {
                        "youtube_url": youtube_url,
                        "song_name": song_name,
                        "artist": artist,

                        # add the uri, easy to get song to put into playlist
                        "spotify_uri": spotify_uri
                    }


# Step 3: Create a new playlist in Spotify
    def create_playlist(self):
        request_body = json.dumps({
            "name": "Youtube",
            "description": "Liked from Youtube",
            "public": True
            })

        query = "https://api.spotify.com/v1/users/{}/playlists".format(self.user_id)
        response = requests.post(
            query,
            data=request_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotify_token)
            }
        )
        response_json = response.json()

        # playlist id
        return response_json["id"]

# Step 4: Search for the song
    def get_spotify_uri(self, song_name, artist):
        query = "https://api.spotify.com/v1/search?query=track%3A{}+artist%3A{}&type=track&offset=0&limit=20".format(
            song_name,
            artist
        )
        response = requests.get(
            query,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotify_token)
            }
        )
        response_json = response.json()
        print(response_json)

        # add verification for empty list
        songs = response_json["tracks"]["items"]
        length = songs.__len__

        if songs:
            print(songs)

            # only use the first song
            uri = songs[0]["uri"]
            print(uri)

            return uri
        else:
            print("List of uri is empty")

# Step 5: Add this song to the spotify playlist
    def add_song_to_playlist(self):

        # populate our songs dictionary
        self.get_liked_videos()

        # collect all of uri
        uris = []
        for song, uri in self.all_song_info.items():
            uris.append(uri["spotify_uri"])

        # create a new list
        playlist_id = self.create_playlist()

        # add all songs into new playlist
        request_data = json.dumps(uris)

        query = "https://api.spotify.com/v1/playlists/{}/tracks".format(playlist_id)
        response = requests.post(
            query,
            data=request_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotify_token)
            }
        )

        # check for valid response status
        if response.status_code != (200 and 201):
            raise Exception(response.status_code)

        response_json = response.json()
        return response_json

    def preset_statistics(self):
        pass

    def present_most_likes(self):
        pass


if __name__ == '__main__':
    cp = CreatePlaylist()
    cp.add_song_to_playlist()