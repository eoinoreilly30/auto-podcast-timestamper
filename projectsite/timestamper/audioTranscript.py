import contextlib
import sys
import os
import logging
import wave
import numpy as np
from projectsite.timestamper import transcriber

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


# aggressiveness integer between 0-3
def transcribe(wavfile_path, model_dir, aggressiveness=1):
    dir_name = os.path.expanduser(model_dir)

    output_graph, scorer = transcriber.resolve_models(dir_name)

    deepspeech_object, model_load_time, scorer_load_time = transcriber.load_model(output_graph, scorer)

    with contextlib.closing(wave.open(wavfile_path, 'rb')) as wav_data:
        segment_generator, sample_rate, audio_length = transcriber.vad_segment_generator(wav_data, aggressiveness)

    sentences = []

    for i, (segment, timestamp) in enumerate(segment_generator):
        logging.debug("Processing chunk %002d" % (i,))
        segment = np.frombuffer(segment, dtype=np.int16)
        inference, time_taken, segment_length = transcriber.stt(deepspeech_object, segment, sample_rate)
        sentences.append((timestamp, inference))

    return sentences
