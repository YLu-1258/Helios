import pafy

plurl = "https://www.youtube.com/playlist?list=PL634F2B56B8C346A2"
playlist = pafy.get_playlist(plurl)
print(playlist["title"])