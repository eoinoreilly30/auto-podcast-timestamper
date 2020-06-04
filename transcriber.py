import contextlib
import os
import logging
import wave
import numpy as np
import glob
import webrtcvad
import collections
from deepspeech import Model
from timeit import default_timer as timer

import config


def read_wave(wf):
    """Reads a .wav file.

    Takes the wav data, and returns (PCM audio data, sample rate).
    """
    num_channels = wf.getnchannels()
    assert num_channels == 1
    sample_width = wf.getsampwidth()
    assert sample_width == 2
    sample_rate = wf.getframerate()
    assert sample_rate in (8000, 16000, 32000)
    frames = wf.getnframes()
    pcm_data = wf.readframes(frames)
    duration = frames / sample_rate
    return pcm_data, sample_rate, duration


def write_wave(path, audio, sample_rate):
    """Writes a .wav file.

    Takes path, PCM audio data, and sample rate.
    """
    with contextlib.closing(wave.open(path, 'wb')) as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio)


class Frame(object):
    """Represents a "frame" of audio data."""

    def __init__(self, bytedata, timestamp, duration):
        self.bytes = bytedata
        self.timestamp = timestamp
        self.duration = duration


def frame_generator(frame_duration_ms, audio, sample_rate):
    """Generates audio frames from PCM audio data.

    Takes the desired frame duration in milliseconds, the PCM data, and
    the sample rate.

    Yields Frames of the requested duration.
    """
    n = int(sample_rate * (frame_duration_ms / 1000.0) * 2)
    offset = 0
    timestamp = 0.0
    duration = (float(n) / sample_rate) / 2.0
    while offset + n < len(audio):
        yield Frame(audio[offset:offset + n], timestamp, duration)
        timestamp += duration
        offset += n


def vad_collector(sample_rate, frame_duration_ms, padding_duration_ms, vad, frames):
    """Filters out non-voiced audio frames.

    Given a webrtcvad.Vad and a source of audio frames, yields only
    the voiced audio.

    Uses a padded, sliding window algorithm over the audio frames.
    When more than 90% of the frames in the window are voiced (as
    reported by the VAD), the collector triggers and begins yielding
    audio frames. Then the collector waits until 90% of the frames in
    the window are unvoiced to de-trigger.

    The window is padded at the front and back to provide a small
    amount of silence or the beginnings/endings of speech around the
    voiced frames.

    Arguments:

    sample_rate - The audio sample rate, in Hz.
    frame_duration_ms - The frame duration in milliseconds.
    padding_duration_ms - The amount to pad the window, in milliseconds.
    vad - An instance of webrtcvad.Vad.
    frames - a source of audio frames (sequence or generator).

    Returns: A generator that yields PCM audio data.
    """
    num_padding_frames = int(padding_duration_ms / frame_duration_ms)
    # We use a deque for our sliding window/ring buffer.
    ring_buffer = collections.deque(maxlen=num_padding_frames)
    # We have two states: TRIGGERED and NOTTRIGGERED. We start in the
    # NOTTRIGGERED state.
    triggered = False

    voiced_frames = []
    for frame in frames:
        is_speech = vad.is_speech(frame.bytes, sample_rate)

        if not triggered:
            ring_buffer.append((frame, is_speech))
            num_voiced = len([f for f, speech in ring_buffer if speech])

            # If we're NOTTRIGGERED and more than 90% of the frames in
            # the ring buffer are voiced frames, then enter the
            # TRIGGERED state.
            if num_voiced > 0.9 * ring_buffer.maxlen:
                triggered = True

                # We want to yield all the audio we see from now until
                # we are NOTTRIGGERED, but we have to start with the
                # audio that's already in the ring buffer.
                for f, s in ring_buffer:
                    voiced_frames.append(f)
                ring_buffer.clear()
        else:
            # We're in the TRIGGERED state, so collect the audio data
            # and add it to the ring buffer.
            voiced_frames.append(frame)
            ring_buffer.append((frame, is_speech))
            num_unvoiced = len([f for f, speech in ring_buffer if not speech])

            # If more than 90% of the frames in the ring buffer are
            # unvoiced, then enter NOTTRIGGERED and yield whatever
            # audio we've collected.
            if num_unvoiced > 0.9 * ring_buffer.maxlen:
                triggered = False
                yield b''.join([f.bytes for f in voiced_frames]), voiced_frames[0].timestamp
                ring_buffer.clear()
                voiced_frames = []

    if triggered:
        pass

    # If we have any leftover voiced audio when we run out of input,
    # yield it.
    if voiced_frames:
        yield b''.join([f.bytes for f in voiced_frames]), voiced_frames[0].timestamp


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
    audio, sample_rate, audio_length = read_wave(wav_data)
    assert sample_rate == 16000, "Only 16000Hz input WAV files are supported for now!"
    vad = webrtcvad.Vad(int(aggressiveness))
    frames = frame_generator(30, audio, sample_rate)
    frames = list(frames)
    segment_generator = vad_collector(sample_rate, 30, 300, vad, frames)

    return segment_generator, sample_rate, audio_length


# aggressiveness integer between 0-3
def transcribe(wavfile_path, model_dir):
    dir_name = os.path.expanduser(model_dir)

    output_graph, scorer = resolve_models(dir_name)

    deepspeech_object, model_load_time, scorer_load_time = load_model(output_graph, scorer)

    with contextlib.closing(wave.open(wavfile_path, 'rb')) as wav_data:
        segment_generator, sample_rate, audio_length = vad_segment_generator(wav_data, config.aggressiveness)

    sentences = []

    for i, (segment, timestamp) in enumerate(segment_generator):
        logging.info("Processing chunk %002d" % (i,))
        segment = np.frombuffer(segment, dtype=np.int16)
        inference, time_taken, segment_length = stt(deepspeech_object, segment, sample_rate)
        logging.debug((timestamp, inference))
        sentences.append((timestamp, inference))

    return sentences
