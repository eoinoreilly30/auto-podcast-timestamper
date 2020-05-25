import logging
import sys
import requests

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


def download(url, request_id):
    logging.debug("starting download: " + str(request_id))
    response = requests.get(url)

    logging.debug("saving file: " + str(request_id))
    filepath = 'requests-files/' + str(request_id) + '/audio.mp3'
    with open(filepath, 'wb') as file:
        file.write(response.content)
