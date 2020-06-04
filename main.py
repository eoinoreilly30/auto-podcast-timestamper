from __future__ import division
from flask import Flask, request, jsonify
import time
import logging
import requests
import transcriber
import summarizer
import os
import config
import helpers
import threading
import uuid

logging.basicConfig(filename='log.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

app = Flask(__name__)


def setup_logger(name, log_file, level=logging.INFO):
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


def download(url, output_filepath, log_stream):
    logging.info("starting download: " + output_filepath)
    log_stream.info("starting download: " + output_filepath)

    response = None
    try:
        response = requests.get(url)
    except requests.exceptions.MissingSchema:
        logging.error('invalid url')
        log_stream.info('invalid url')

    logging.info("saving file: " + output_filepath)
    log_stream.info("saving file: " + output_filepath)
    with open(output_filepath, 'wb') as file:
        file.write(response.content)


def transcribe_into_paragraphs(wavfile_path, model_dir, minute_increment, log_stream):
    log_stream.info('beginning transcription: ' + wavfile_path)
    logging.info('beginning transcription: ' + wavfile_path)
    sentences = transcriber.transcribe(wavfile_path, model_dir, log_stream)

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


def convert_and_resample(audio_filepath, log_stream):
    basedir = os.path.dirname(audio_filepath) + '/'

    log_stream.info('converting to wav: ' + audio_filepath)
    logging.info('converting to wav: ' + audio_filepath)
    wav_filepath = basedir + 'tmp.wav'
    helpers.mp3towav(audio_filepath, wav_filepath)

    log_stream.info('resampling to 16kHz: ' + audio_filepath)
    logging.info('resampling to 16kHz: ' + audio_filepath)
    resampled_wav_filepath = basedir + 'audio.wav'
    helpers.change_sample_rate(wav_filepath, resampled_wav_filepath, 16000, 1)


def handle_request(download_link, request_id, minute_increment, log_stream):
    request_dir = config.root_dir + request_id + '/'
    audio_filepath = request_dir + 'audio.mp3'
    model_dir = config.model_dir

    os.makedirs(request_dir, exist_ok=True)

    download(download_link, audio_filepath, log_stream)
    convert_and_resample(audio_filepath, log_stream)

    wav_filepath = request_dir + 'audio.wav'
    paragraphs = transcribe_into_paragraphs(wav_filepath, model_dir, minute_increment, log_stream)
    summary = summarize(paragraphs, request_dir, model_dir)
    log_stream.info(summary)


@app.route('/request', methods=['POST'])
def receive_request():
    request_id = str(uuid.uuid1())
    download_link = request.json['url']
    minute_increment = request.json['minute_increment']

    os.makedirs(config.root_dir + request_id + '/', exist_ok=True)

    log_file = config.root_dir + request_id + '/stream.log'
    log_stream = setup_logger('log_stream', log_file)

    thread = threading.Thread(target=handle_request, args=(download_link, request_id, minute_increment, log_stream))
    thread.start()

    response = jsonify({'request_id': request_id})
    return response, 202


@app.route('/stream/<string:request_id>', methods=['GET'])
def stream(request_id):
    def generate():
        with open(config.root_dir + request_id + '/stream.log') as f:
            while True:
                yield f.read()
                time.sleep(1)

    return app.response_class(generate(), mimetype='text/plain')
