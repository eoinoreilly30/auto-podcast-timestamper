from __future__ import division
from flask import Flask, request
import logging
import requests
import transcriber
import summarizer
import os
import config
import helpers

logging.basicConfig(filename='log.log', level=logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

app = Flask(__name__)


def setup_logger(name, log_file, level=logging.INFO):
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


def download(url, output_filepath):
    logging.info("starting download: " + output_filepath)
    response = requests.get(url)

    logging.info("saving file: " + output_filepath)
    with open(output_filepath, 'wb') as file:
        file.write(response.content)


def transcribe_into_paragraphs(wavfile_path, model_dir, minute_increment):
    logging.info('beginning transcription: ' + wavfile_path)
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

    return paragraphs


def summarize(paragraphs, request_dir, model_dir):
    logging.info('beginning summary: ' + request_dir)
    summary = []
    for paragraph in paragraphs:
        # split paragraph up if too big
        if len(paragraph) > config.summarizer_max_characters:
            step = config.summarizer_max_characters
            tmp_summary = ''
            for i in range(0, len(paragraph), step):
                tmp_summary += summarizer.summarize(paragraph[i:i + step], request_dir, model_dir)

            summary.append(tmp_summary)
        else:
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
    paragraphs = transcribe_into_paragraphs(wav_filepath, model_dir, minute_increment=5)
    summary = summarize(paragraphs, request_dir, model_dir)

    return "test"
