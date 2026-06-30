'''
the robot will have speech enabled, so this module turns the robot's chosen
utterances into spoken audio (text-to-speech) as well as returning the text.
'''

try:
    import pyttsx3
except ImportError:                  # library not installed yet
    pyttsx3 = None


class NLG:
    '''
    Goal: generate spoken responses to the user.

    Uses pyttsx3 -- a free, offline TTS engine (no API key, no internet; espeak
    on Linux). If pyttsx3 is missing or no audio device is available the text is
    still returned, so the dialogue keeps working silently.
    '''
    def __init__(self, use_voice: bool = True, rate: int = 165):
        ## TTS shares the single voice switch with the NLU's ASR: off means the
        ## dialogue still runs, just silently (text is always returned/printed).
        self.use_voice = use_voice
        self.rate = rate
        if use_voice and pyttsx3 is None:
            print("[TTS unavailable: `pip install pyttsx3`. Continuing silently.]")
            self.use_voice = False
        elif use_voice:
            ## Validate that a working engine can be built; we don't keep it.
            ## pyttsx3's run loop is single-shot -- after one runAndWait() a
            ## reused engine goes silent (notably the macOS nsss driver), so
            ## speak() builds a fresh engine per utterance instead.
            try:
                self._make_engine()
            except Exception as exc:                     # no audio device, bad driver, ...
                print(f"[TTS disabled: {exc}]")
                self.use_voice = False

    def _make_engine(self):
        '''Build a fresh pyttsx3 engine configured with the current rate.'''
        engine = pyttsx3.init()
        engine.setProperty('rate', self.rate)   # speaking speed (words/min)
        return engine

    def speak(self, text: str):
        '''Read any system output aloud when TTS is on; a no-op otherwise.'''
        if text and self.use_voice:
            engine = self._make_engine()
            engine.say(text)
            engine.runAndWait()
            engine.stop()

    def process(self, utterance: str):
        '''Speak the robot's chosen utterance, and return the text for display.'''
        self.speak(utterance)
        return utterance
