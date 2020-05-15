import sys

from pydub import AudioSegment

src = sys.argv[1]
dest = sys.argv[2]

sound = AudioSegment.from_mp3(src)
sound.export(dest, format="wav")

print("success")
