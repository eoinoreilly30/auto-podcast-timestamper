from __future__ import division
from flask import Flask, request
import logging
import requests
import transcriber
import summarizer
import os
import config
import helpers

logging.basicConfig(filename='logs.log', level=logging.DEBUG)
app = Flask(__name__)


def download(url, output_filepath):
    logging.info("starting download: " + output_filepath)
    response = requests.get(url)

    logging.info("saving file: " + output_filepath)
    with open(output_filepath, 'wb') as file:
        file.write(response.content)


def transcribe_and_summarize(wavfile_path, request_dir, model_dir, minute_increment=5):
    sentences = transcriber.transcribe(wavfile_path, model_dir)

    increment = minute_increment * 60
    paragraphs = []
    paragraph = ''
    for (timestamp, sentence) in sentences:
        paragraph += (' ' + sentence)

        if timestamp / increment > 1:
            paragraphs.append(paragraph)
            increment += increment
            paragraph = ''

    logging.info('beginning summary: ' + request_dir)
    summary = []
    for paragraph in paragraphs:
        summary.append(summarizer.summarize(paragraph, request_dir, model_dir))

    summary = [x.replace('[X_SEP]', '') for x in summary]
    return summary


def convert_and_resample(audio_filepath):
    basedir = os.path.dirname(audio_filepath) + '/'

    logging.info('converting to wav: ' + audio_filepath)
    wav_filepath = basedir + 'tmp.wav'
    helpers.mp3towav(audio_filepath, wav_filepath)

    logging.info('resampling to 16kHz: ' + audio_filepath)
    resampled_wav_filepath = basedir + 'audio.wav'
    helpers.change_sample_rate(wav_filepath, resampled_wav_filepath, 16000, 1)


@app.route('/', methods=['POST'])
def index():
    download_link = request.form['url']
    request_id = "1"
    request_dir = config.root_dir + request_id + '/'
    audio_filepath = request_dir + 'audio.mp3'
    wav_filepath = request_dir + 'audio.wav'
    model_dir = config.model_dir

    os.makedirs(request_dir, exist_ok=True)

    convert_and_resample(audio_filepath)

    download(download_link, audio_filepath)
    transcribe_and_summarize(wav_filepath, request_dir, model_dir, minute_increment=5)

    return "test"
