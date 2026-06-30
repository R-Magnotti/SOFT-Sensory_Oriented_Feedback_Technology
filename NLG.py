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
    def __init__(self, rate: int = 165):
        self.engine = None
        if pyttsx3 is not None:
            try:
                self.engine = pyttsx3.init()
                self.engine.setProperty('rate', rate)   # speaking speed (words/min)
            except Exception as exc:                     # no audio device, bad driver, ...
                print(f"[TTS disabled: {exc}]")

    def process(self, utterance: str):
        '''Speak the robot's chosen utterance, and return the text for display.'''
        if utterance and self.engine is not None:
            self.engine.say(utterance)
            self.engine.runAndWait()
        return utterance
