from __future__ import division

import os

from flask import Flask, request
import logging
import sys
import requests
import transcriber
import summarizer

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
app = Flask(__name__)


def download(url, output_filepath):
    logging.debug("starting download: " + output_filepath)
    response = requests.get(url)

    logging.debug("saving file: " + output_filepath)
    with open(output_filepath, 'wb') as file:
        file.write(response.content)


def transcribe_and_summarize(download_link, request_id, minute_increment=5):
    request_dir = '/dev/shm/' + request_id + '/'
    audio_filepath = request_dir + 'audio.mp3'
    model_dir = "projectsite/timestamper/models/"

    os.makedirs(request_dir, exist_ok=True)

    download(download_link, audio_filepath)

    sentences = transcriber.transcribe(audio_filepath, model_dir)

    increment = minute_increment * 60
    paragraphs = []
    paragraph = ''
    for (timestamp, sentence) in sentences:
        paragraph += (' ' + sentence)

        if timestamp / increment > 1:
            paragraphs.append(paragraph)
            increment += increment
            paragraph = ''

    summary = []
    for paragraph in paragraphs:
        summary.append(summarizer.summarize(paragraph, request_dir, model_dir))

    return summary


@app.route('/', methods=['POST'])
def index():
    print(request.form['url'])
    return "test"
