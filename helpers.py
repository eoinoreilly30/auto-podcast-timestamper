import os
import subprocess
import wave


def mp3towav(mp3_path, wav_path):
    subprocess.run(
        ['/usr/bin/ffmpeg', '-loglevel', 'warning', '-hide_banner', '-y', '-i', mp3_path, '-acodec', 'pcm_s16le', '-ac', '1',
         '-ar', '16000', wav_path])


def get_wav_sample_rate(wav_path):
    with wave.open(wav_path, "rb") as wave_file:
        return wave_file.getframerate()


def change_sample_rate(input_file, output_file, new_sample_rate, channels):
    command = 'ffmpeg -loglevel warning -hide_banner -y -i ' + input_file + \
              ' -ar ' + str(new_sample_rate) + \
              ' -ac ' + str(channels) + \
              ' ' + output_file
    os.system(command)
