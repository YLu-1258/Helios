import requests
import lxml.etree
import json
import re
from enum import Enum


class InvalidLink(Exception):
    pass

class LinkType(Enum):
    YOUTUBE = "YouTube"
    YOUTUBE_PLAYLIST = "YouTube Playlist"
    SPOTIFY = "Spotify"
    SPOTIFY_PLAYLIST = "Spotify Playlist"
    UNKNOWN = "Unkown"

def sortLink(url):
    if "https://open.spotify.com/track" in url:
        return LinkType.SPOTIFY
    if "https://open.spotify.com/playlist" in url:
        return LinkType.SPOTIFY_PLAYLIST
    if "https://www.youtu" in url or "https://youtu.be" in url:
        if "https://www.youtube.com/playlist?list=" in url:
            return LinkType.YOUTUBE_PLAYLIST
        return LinkType.YOUTUBE
    
    
    return LinkType.UNKNOWN
    

def processMobile(url):
    if url.startswith("https://m."):
        return url.replace("https://m.", "https://")
    elif url.startswith("http://m."):
        return url.replace("http://m.", "http://")
    raise InvalidLink

def getSongs(url):
    results = []
    def getIDs(url):
        raw = requests.get(url).text
        js = lxml.etree.HTML(raw).findall('.//body/script')
        for i in js:
            if "ytInitialData" in str(i.text):
                data = json.loads(i.text[20:-1])
                break
        json_object = json.dumps(data, indent = 4)
        return json_object

    def build_list(a_dict):
        try:
            if "https://www.youtube.com/watch?v="+a_dict['videoId'] not in results:
                results.append("https://www.youtube.com/watch?v="+a_dict['videoId'])
        except KeyError:
            pass
        return a_dict

    json.loads(getIDs(url), object_hook=build_list)
    
    return results

def validUrl(query):
    url_re = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    return re.match(url_re, query) is not None

def check_lyric(title,author):
    URL_SEARCH = "https://some-random-api.ml/lyrics?title="

    
