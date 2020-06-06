from __future__ import division
from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
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
CORS(app)


def exit_stream(log_stream, request_dir=''):
    with open(log_stream, 'a') as f:
        f.write("EXIT_CODE")
    result = subprocess.run(['rm', '-rf', request_dir])
    if result.returncode == 0:
        logging.info('Successfully cleaned up')
    else:
        logging.error('Error cleaning up')


def download(url, output_filepath, log_stream):
    logging.info("Starting download: " + output_filepath)
    with open(log_stream, 'a') as f:
        f.write("\nStarting download\n")

    response = None
    try:
        response = requests.get(url)
    except requests.exceptions.MissingSchema:
        logging.error('Invalid url')
        with open(log_stream, 'a') as f:
            f.write('\nInvalid url\n')
        exit_stream(log_stream)

    with open(log_stream, 'a') as f:
        f.write("\nSaving file\n")
    logging.info("Saving file: " + output_filepath)

    with open(output_filepath, 'wb') as file:
        file.write(response.content)


def convert_and_resample(audio_filepath, log_stream):
    basedir = os.path.dirname(audio_filepath) + '/'

    with open(log_stream, 'a') as f:
        f.write('\nConverting to wav\n')
    logging.info('Converting to wav: ' + audio_filepath)

    wav_filepath = basedir + 'tmp.wav'
    helpers.mp3towav(audio_filepath, wav_filepath)

    with open(log_stream, 'a') as f:
        f.write('\nResampling to 16kHz\n')
    logging.info('Resampling to 16kHz: ' + audio_filepath)

    resampled_wav_filepath = basedir + 'audio.wav'
    helpers.change_sample_rate(wav_filepath, resampled_wav_filepath, 16000, 1)


def transcribe_into_paragraphs(wavfile_path, model_dir, minute_increment, log_stream):
    with open(log_stream, 'a') as f:
        f.write('\nBeginning transcription\n')
    logging.info('Beginning transcription: ' + wavfile_path)

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


def summarize(paragraphs, request_dir, model_dir, log_stream):
    with open(log_stream, 'a') as f:
        f.write('\nBeginning summary\n')
    logging.info('Beginning summary: ' + request_dir)

    summary = []
    for idx, paragraph in enumerate(paragraphs):
        with open(log_stream, 'a') as f:
            f.write('\nProcessing summary %002d\n' % idx)

        # split paragraph up if too big
        if len(paragraph) > config.summarizer_max_characters:
            step = config.summarizer_max_characters
            tmp_summary = ''
            for i in range(0, len(paragraph), step):
                tmp_summary += summarizer.summarize(paragraph[i:i + step], request_dir, model_dir, log_stream)

            summary.append(tmp_summary)
        else:
            summary.append(summarizer.summarize(paragraph, request_dir, model_dir, log_stream))

    return summary


def handle_request(download_link, request_id, minute_increment, log_stream):
    request_dir = config.root_dir + request_id + '/'
    audio_filepath = request_dir + 'audio.mp3'
    model_dir = config.model_dir

    os.makedirs(request_dir, exist_ok=True)

    # download(download_link, audio_filepath, log_stream)
    # convert_and_resample(audio_filepath, log_stream)

    wav_filepath = request_dir + 'audio.wav'
    paragraphs = transcribe_into_paragraphs('audio-examples/joe-voice.wav', model_dir, minute_increment, log_stream)
    summary = summarize(paragraphs, request_dir, model_dir, log_stream)

    with open(log_stream, 'a') as f:
        f.write('\nFull Summary:\n')
        for idx, line in enumerate(summary):
            f.write('\n%.2f-%.2f\n' % (idx * minute_increment, (idx + 1) * minute_increment))
            f.write('\n' + line + '\n')

    with open(log_stream, 'a') as f:
        f.write('\nProcess Finished, please exit\n')

    exit_stream(log_stream, request_dir)

    return


@app.route('/request', methods=['POST'])
def receive_request():
    request_id = str(uuid.uuid1())

    try:
        download_link = request.json['url']
        print(download_link)
        minute_increment = float(request.json['minute_increment'])
    except KeyError:
        return "Missing parameters", 400

    os.makedirs(config.root_dir + request_id + '/', exist_ok=True)

    log_stream = config.root_dir + request_id + '/stream.log'
    with open(log_stream, 'a') as f:
        f.write('Start\n')

    thread = threading.Thread(target=handle_request, args=(download_link, request_id, minute_increment, log_stream))
    thread.start()

    response = jsonify({'request_id': request_id})
    return response, 202


@app.route('/stream/<string:request_id>', methods=['GET'])
def stream(request_id):
    stream_filepath = config.root_dir + request_id + '/stream.log'
    if not os.path.isfile(stream_filepath):
        return "Stream not found", 404

    def generate():
        with open(stream_filepath, 'r') as f:
            while True:
                line = str(f.read())
                if line == 'EXIT_CODE':
                    raise StopIteration
                else:
                    yield line
                time.sleep(1)

    return app.response_class(generate(), mimetype='text/plain')


@app.route('/', methods=['GET'])
def index():
    return "Welcome to the Auto Podcast Timestamper API\n"
