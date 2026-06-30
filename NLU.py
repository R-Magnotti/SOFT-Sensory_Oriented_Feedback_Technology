import queue
from typing import Optional, Sequence, TypeVar

from matchers import FuzzyMatcher, HasUtterances, UtteranceMatcher

## Speech-to-text stack, all pip-installable (no system dev headers, no conda):
##   sounddevice -- records from the mic via the system libportaudio at runtime
##   SpeechRecognition -- transcribes via Google's free Web Speech endpoint (needs net)
try:
    import sounddevice as sd
    import numpy as np
    import speech_recognition as sr
except ImportError:                  # one or more voice libs not installed yet
    sd = np = sr = None

## an option is anything exposing representative `.utterances` (e.g. graph.Option)
Opt = TypeVar("Opt", bound=HasUtterances)

SAMPLE_RATE = 16000      # Hz -- ample for speech and what Google's recogniser expects
RECORD_SECONDS = 5       # fixed push-to-talk window captured per turn
CHUNK_SECONDS = 1.5      # re-transcribe and print the growing buffer this often


class NLU:
    '''NLU module: ASR, discourse tracking, and matching user text to dialogue options.'''
    def __init__(self, context, matcher: Optional[UtteranceMatcher] = None,
                 use_voice: bool = False, record_seconds: float = RECORD_SECONDS,
                 chunk_seconds: float = CHUNK_SECONDS):
        self.context = context
        ## the matcher is a swappable strategy: fuzzy today, an LM/classifier later
        self.matcher = matcher or FuzzyMatcher()

        ## speech-to-text setup
        self.use_voice = use_voice
        self.record_seconds = record_seconds
        self.chunk_seconds = chunk_seconds
        self.recognizer = None
        if use_voice and (sd is None or np is None or sr is None):
            print("[ASR unavailable: `pip install sounddevice SpeechRecognition numpy`. Falling back to typing.]")
            self.use_voice = False
        elif use_voice:
            try:
                self.recognizer = sr.Recognizer()
                sd.check_input_settings(samplerate=SAMPLE_RATE, channels=1)  # verify a mic exists
            except Exception as exc:                 # no input device, bad portaudio, ...
                print(f"[ASR disabled ({exc}); falling back to typing.]")
                self.use_voice = False

    def process(self, speech):
        '''
        Goal: pass user speech input through the NL pipeline; returns recognised text.
        '''
        utterances = self.ASR(speech)
        self.update_LF(utterances)
        return utterances

    def ASR(self, speech):
        '''
        Params:
            speech: text typed at the prompt (a manual override), or "" to capture
                from the microphone in voice mode.
        Goal: convert spoken audio to text using an off-the-shelf ASR tool.

        Anything typed is passed straight through (this is also the path when
        voice is disabled). An empty line in voice mode is push-to-talk: record a
        short window from the mic and transcribe it incrementally, printing the
        transcription as it grows so the user sees words appear while speaking.
        '''
        if speech or not self.use_voice:
            return speech
        print(f"[listening -- speak now ({self.record_seconds:g}s)]")
        try:
            return self._stream_transcribe()
        except Exception as exc:                     # mic vanished mid-run, etc.
            print(f"[mic error: {exc}]")
            return ""

    def _stream_transcribe(self):
        '''
        Goal: capture the mic continuously and print the transcription as it is
        captured, re-transcribing the growing buffer every `chunk_seconds`.

        Audio is collected on a background callback thread (so nothing is dropped
        while a chunk is out for recognition), and each pass re-transcribes the
        whole prefix captured so far -- this keeps partials clean at the seams
        (no words lost between chunks) at the cost of a few extra requests over a
        short window. Returns the final transcription.
        '''
        total_frames = int(self.record_seconds * SAMPLE_RATE)
        chunk_frames = int(self.chunk_seconds * SAMPLE_RATE)
        audio_q: queue.Queue = queue.Queue()

        ## runs on PortAudio's thread: hand the raw int16 PCM off to the consumer
        def on_audio(indata, frames, time_info, status):
            audio_q.put(indata.tobytes())

        buffer = bytearray()
        captured = since_chunk = 0
        text = ""
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16",
                            callback=on_audio):
            while captured < total_frames:
                data = audio_q.get()
                buffer.extend(data)
                n = len(data) // 2               # 2 bytes per int16 sample
                captured += n
                since_chunk += n
                if since_chunk >= chunk_frames:
                    since_chunk = 0
                    partial = self._transcribe_chunk(bytes(buffer))
                    if partial:
                        text = partial
                        print(f"[hearing: {text}]")

        ## final pass over everything captured (incl. the tail after the last chunk)
        final = self._transcribe_chunk(bytes(buffer))
        if final:
            text = final
        if text:
            print(f"[heard: {text}]")
        else:
            print("[couldn't make that out]")
        return text

    def _transcribe_chunk(self, raw_pcm: bytes) -> str:
        '''Transcribe one buffer of raw 16-bit PCM; "" if unintelligible/failed.'''
        audio = sr.AudioData(raw_pcm, SAMPLE_RATE, 2)
        try:
            return self.recognizer.recognize_google(audio)  # free Google endpoint, no API key
        except sr.UnknownValueError:                         # speech was unintelligible
            return ""
        except sr.RequestError as exc:                       # network / endpoint problem
            print(f"[ASR error: {exc}]")
            return ""

    def update_LF(self, utts: str):
        '''
        Goal: use most recent utterances to update relevant discourse information
        '''
        self.context.add_utterance(utts)

    def select(self, text: str, options: Sequence[Opt]) -> Optional[Opt]:
        '''
        Goal: map user text to the closest representative utterance across the
        options available at the current state, and return the owning option.
        Returns None when nothing matches well enough (caller takes the fallback).
        '''
        pairs = [(opt, utterance) for opt in options for utterance in opt.utterances]
        if not pairs:
            return None
        result = self.matcher.match(text, [utterance for _, utterance in pairs])
        if result.candidate is None:
            return None
        return next(opt for opt, utterance in pairs if utterance == result.candidate)
