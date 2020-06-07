# Auto Podcast Timestamper
A service that gives timestamped highlights of an audio clip

Uses:
- [Mozilla DeepSpeech](https://github.com/mozilla/DeepSpeech) for VAD and speech-to-text translation
- [Microsoft ProphetNet](https://github.com/microsoft/prophetnet) for text summarization

## Installation
- ```sudo apt install sox ffmpeg```
#### Install whatever version of pytorch suits your system
- ```pip install torch==1.5.0+cpu -f https://download.pytorch.org/whl/torch_stable.html```
- ```pip install -r requirements.txt```
#### Download models
- ```curl -L https://github.com/mozilla/DeepSpeech/releases/download/v0.7.3/deepspeech-0.7.3-models.pbmm --output models/deepspeech-0.7.3-models.pbmm```
- ```curl -L https://github.com/mozilla/DeepSpeech/releases/download/v0.7.3/deepspeech-0.7.3-models.scorer --output models/deepspeech-0.7.3-models.scorer```
- ```python download_models.py```
