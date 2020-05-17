import os
import wave
from pydub import AudioSegment


def mp3towav(mp3_path, wav_path):
    sound = AudioSegment.from_mp3(mp3_path)
    sound.export(wav_path, format="wav")


def get_wav_sample_rate(wav_path):
    with wave.open(wav_path, "rb") as wave_file:
        return wave_file.getframerate()


def change_sample_rate(input_file, output_file, new_sample_rate, channels):
    command = 'ffmpeg -i ' + input_file + \
              ' -ar ' + str(new_sample_rate) + \
              ' -ac ' + str(channels) + \
              ' ' + output_file
    print(command)
    os.system(command)
