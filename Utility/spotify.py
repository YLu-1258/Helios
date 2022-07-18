
import spotipy
import re
from urllib import request
from urllib.parse import quote 
from spotipy.oauth2 import SpotifyClientCredentials
from options import SPOTIFY_ID, SPOTIFY_SECRET

'''
NOTES:
playlist_tracks(playlist_id, fields=None, limit=100, offset=0, market=None, additional_types=('track', ))

'''

class SpotifyToYoutube:
    def __init__(self):
        self.sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(client_id=SPOTIFY_ID, client_secret=SPOTIFY_SECRET))


    def link_from_names(self, name, artist):
        query = "https://www.youtube.com/results?search_query=" + quote(name) + "+by+" + quote(artist)
        raw = request.urlopen(query)
        video_id = re.findall(r"watch\?v=(\S{11})", raw.read().decode())[0]
        return "https://www.youtube.com/watch?v=" + video_id

    def link_to_yt(self, url):
        track = self.sp.track(url)
        artist = track.get("album").get("artists")[0].get("name").lower().replace(" ", "+")
        track_name = track.get("album").get("name").lower().replace(" ", "+")
        return self.link_from_names(track_name, artist)

    def playlist_to_yt(self, url):
        playlist = self.sp.playlist_tracks(url)
        plist = []
        for i in playlist.get("items"):
            plist.append((i.get("track").get("album").get("artists")[0].get("name").lower().replace(" ", "+"), i.get("track").get("album").get("name").lower().replace(" ", "+")))

        yt_playlist = [self.link_from_names(track[1], track[0]) for track in plist]

        return yt_playlist
