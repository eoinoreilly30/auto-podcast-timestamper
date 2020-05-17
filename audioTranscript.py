import contextlib
import sys
import os
import logging
import wave

import numpy as np
import wavTranscriber

# Debug helpers
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


def transcribe(wavfile_path, model_dir, aggressiveness):
    # Point to a path containing the pre-trained models & resolve ~ if used
    dir_name = os.path.expanduser(model_dir)

    # Resolve all the paths of model files
    output_graph, scorer = wavTranscriber.resolve_models(dir_name)

    # Load output_graph, alphabet and scorer
    deepspeech_object, model_load_time, scorer_load_time = wavTranscriber.load_model(output_graph, scorer)

    inference_time = 0.0

    with contextlib.closing(wave.open(wavfile_path, 'rb')) as wav_data:
        # Run VAD on the wav data
        segments, sample_rate, audio_length = wavTranscriber.vad_segment_generator(wav_data, aggressiveness)

        for i, segment in enumerate(segments):
            # Run deepspeech on the chunk that just completed VAD
            logging.debug("Processing chunk %002d" % (i,))
            audio = np.frombuffer(segment, dtype=np.int16)
            inference, time_taken, segment_length = wavTranscriber.stt(deepspeech_object, audio, sample_rate)
            inference_time += time_taken
            logging.debug("Transcript: %s" % inference)
