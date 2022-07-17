
# importing pafy
import pafy
from discord import FFmpegPCMAudio

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn'}

# url of video
url = "https://www.youtube.com/watch?v=2vuviPLn7ls"
   
# instant created
video = pafy.new(url)
 
# getting number of likes
audio = video.getbestaudio()
print("Audio Retrieved")
source = FFmpegPCMAudio(audio.url, **FFMPEG_OPTIONS)
print("FFmpeg Suceeded!")
audio.download()
print("download suceeded!")
 
# showing likes
print("Suceeded!")