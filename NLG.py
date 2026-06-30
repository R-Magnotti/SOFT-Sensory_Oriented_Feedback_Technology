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
        self.engine = None
        if use_voice and pyttsx3 is None:
            print("[TTS unavailable: `pip install pyttsx3`. Continuing silently.]")
            self.use_voice = False
        elif use_voice:
            try:
                self.engine = pyttsx3.init()
                self.engine.setProperty('rate', rate)   # speaking speed (words/min)
            except Exception as exc:                     # no audio device, bad driver, ...
                print(f"[TTS disabled: {exc}]")
                self.use_voice = False

    def speak(self, text: str):
        '''Read any system output aloud when TTS is on; a no-op otherwise.'''
        if text and self.engine is not None:
            self.engine.say(text)
            self.engine.runAndWait()

    def process(self, utterance: str):
        '''Speak the robot's chosen utterance, and return the text for display.'''
        self.speak(utterance)
        return utterance
