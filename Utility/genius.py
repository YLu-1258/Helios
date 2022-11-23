from lyricsgenius import Genius

Client_Token = "_osY5nFvpXfjG6JI_SFze8JCa8mBDIqiSWkAxawPsAHI4Yti1kzakEK4zcQS4fCX"

class Genius_Client:
    def __init__ (self):
        self.gclient = Genius(Client_Token)

    def get_lyric(self, title):
        song = self.gclient.search_song(title)

        return song