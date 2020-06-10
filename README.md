# Auto Podcast Timestamper
A service that gives timestamped highlights of an audio clip

Frontend hosted @ [eoinor.xyz](https://eoinor.xyz/auto-podcast-timestamper)
API @ [autotimestamper.xyz](https://autotimestamper.xyz)

Uses:
- [Mozilla DeepSpeech](https://github.com/mozilla/DeepSpeech) for VAD and speech-to-text translation
- [Microsoft ProphetNet](https://github.com/microsoft/prophetnet) for text summarization

## Installation
- ```sudo apt install sox ffmpeg```
#### Install whatever version of PyTorch suits your system
- ```pip install torch==1.5.0+cpu -f https://download.pytorch.org/whl/torch_stable.html```
- ```pip install -r requirements.txt```
#### Download models
- ```mkdir models/```
- ```curl -L https://github.com/mozilla/DeepSpeech/releases/download/v0.7.3/deepspeech-0.7.3-models.pbmm --output models/deepspeech-0.7.3-models.pbmm```
- ```curl -L https://github.com/mozilla/DeepSpeech/releases/download/v0.7.3/deepspeech-0.7.3-models.scorer --output models/deepspeech-0.7.3-models.scorer```
- ```python download_models.py```

## Usage
Run as Flask API
- ```export FLASK_APP=main.py```
- ```flask run```

## API
#### Request
```POST /request```

Parameters:
- url: A download URL from Acast for the podcast
- minute_increment: How often to timestamp

```curl -X POST -d '{"url": "<URL>", "minute_increment": "<INT>"}' -H 'Content-Type: application/json' http://localhost:5000/request```

Response

```"{request_id: <UUID>}"```

#### Stream the response back
```GET /stream/<request-id>```

```curl -X GET http://localhost:5000/stream/<request-id>```

Response

```Either let it stream to your terminal or handle with JS Stream API```
