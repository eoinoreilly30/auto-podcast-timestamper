from __future__ import division
import logging
import sys
import requests
from projectsite.timestamper import transcriber, summarizer

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


def download(url, output_filepath):
    logging.debug("starting download: " + output_filepath)
    response = requests.get(url)

    logging.debug("saving file: " + output_filepath)
    with open(output_filepath, 'wb') as file:
        file.write(response.content)


def transcribe_and_summarize(download_link, request_id, minute_increment=5):
    audio_filepath = '/dev/shm/' + str(request_id) + '/audio.mp3'
    download(download_link, audio_filepath)

    increment = minute_increment * 60

    sentences = transcriber.transcribe(audio_filepath, "projectsite/timestamper/models")

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
        summary.append(summarizer.summarize(paragraph, request_id))

    return summary
