import requests


def download_file_from_google_drive(id, destination):
    url = "https://docs.google.com/uc?export=download"

    session = requests.Session()

    response = session.get(url, params={'id': id}, stream=True)
    token = get_confirm_token(response)

    if token:
        params = {'id': id, 'confirm': token}
        response = session.get(url, params=params, stream=True)

    save_response_content(response, destination)


def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value

    return None


def save_response_content(response, destination):
    CHUNK_SIZE = 32768

    with open(destination, "wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)


print('downloading cnn/dm')
download_file_from_google_drive('14v0HMc7obh_5aPFSFWzcr_nZCrK49Sey', 'models/cnndm.pt')

# mkdir models
# curl -L https://github.com/mozilla/DeepSpeech/releases/download/v0.7.3/deepspeech-0.7.3-models.pbmm --output models/deepspeech-0.7.3-models.pbmm
# curl -L https://github.com/mozilla/DeepSpeech/releases/download/v0.7.3/deepspeech-0.7.3-models.scorer --output models/deepspeech-0.7.3-models.scorer