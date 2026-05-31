import moviepy.editor as mp
import os

# video = mp.VideoFileClip("./test.mp4")    # 此处为视频的绝对路径。
# video.audio.write_audiofile('./test.wav', bitrate="8k")

command = f"ffmpeg -loglevel quiet -i test.mp3 -ac 1 -ar 16000 test.wav -y"
os.system(command)