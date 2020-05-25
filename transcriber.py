import glob
import webrtcvad
import logging
import split
from deepspeech import Model
from timeit import default_timer as timer

'''
Load the pre-trained model into the memory
@param models: Output Graph Protocol Buffer file
@param scorer: Scorer file

@Retval
Returns a list [DeepSpeech Object, Model Load Time, Scorer Load Time]
'''


def load_model(models, scorer):
    model_load_start = timer()
    ds = Model(models)
    model_load_end = timer() - model_load_start
    logging.debug("Loaded model in %0.3fs." % model_load_end)

    scorer_load_start = timer()
    ds.enableExternalScorer(scorer)
    scorer_load_end = timer() - scorer_load_start
    logging.debug('Loaded external scorer in %0.3fs.' % scorer_load_end)

    return [ds, model_load_end, scorer_load_end]


'''
Run Inference on input audio file
@param ds: Deepspeech object
@param audio: Input audio for running inference on
@param fs: Sample rate of the input audio file

@Retval:
Returns a list [Inference, Inference Time]

'''


def stt(ds, audio, fs):
    inference_time = 0.0
    segment_length = len(audio) * (1 / fs)

    # Run Deepspeech
    # logging.debug('Running inference...')
    inference_start = timer()
    output = ds.stt(audio)
    inference_end = timer() - inference_start
    inference_time += inference_end
    # logging.debug('Inference took %0.3fs for %0.3fs audio file.' % (inference_end, segment_length))

    return [output, inference_time, segment_length]


'''
Resolve directory path for the models and fetch each of them.
@param dirName: Path to the directory containing pre-trained models

@Retval:
Returns a tuple containing each of the model files (pb, scorer)
'''


def resolve_models(dirname):
    pb = glob.glob(dirname + "/*.pbmm")[0]
    logging.debug("Found Model: %s" % pb)

    scorer = glob.glob(dirname + "/*.scorer")[0]
    logging.debug("Found scorer: %s" % scorer)

    return pb, scorer


'''
Generate VAD segments. Filters out non-voiced audio frames.
@param waveFile: Input wav file to run VAD on.0

@Retval:
Returns tuple of
    segments: a byte array of multiple smaller audio frames
              (The longer audio split into multiple smaller one's)
    sample_rate: Sample rate of the input audio file
    audio_length: Duration of the input audio file

'''


def vad_segment_generator(wav_data, aggressiveness):
    audio, sample_rate, audio_length = split.read_wave(wav_data)
    assert sample_rate == 16000, "Only 16000Hz input WAV files are supported for now!"
    vad = webrtcvad.Vad(int(aggressiveness))
    frames = split.frame_generator(30, audio, sample_rate)
    frames = list(frames)
    segment_generator = split.vad_collector(sample_rate, 30, 300, vad, frames)

    return segment_generator, sample_rate, audio_length