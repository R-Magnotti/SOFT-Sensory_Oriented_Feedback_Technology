from NLU import NLU
from NLG import NLG
from deliberate import StoryEngine
from graph import StoryGraph
from context import DiscourseContext
import os
import socket
import struct

SCRIPT = "wound_cleaning.json"

## Voice I/O (mic speech-to-text + spoken text-to-speech) is on by default.
## Set SOFT_VOICE=0 to run the old type-only loop (e.g. headless / CI).
USE_VOICE = os.environ.get("SOFT_VOICE", "1") != "0"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(struct.pack("<dd", 1, 0), ("127.0.0.1", 5005))

class Robot:
    def __init__(self, script=SCRIPT, use_voice=USE_VOICE):
        ## shared dialogue state, written by NLU
        self.context = DiscourseContext()

        ## NLP + dialogue modules. The engine walks the graph; the NLU matches
        ## user replies to the branches the engine offers.
        self.nlu = NLU(self.context, use_voice=use_voice)
        self.nlg = NLG()
        self.engine = StoryEngine(StoryGraph.from_file(script))
        ## reflect what the NLU actually enabled (it may have fallen back to text)
        self.use_voice = self.nlu.use_voice

    def run(self):
        '''Drive the vignette: speak each beat, then read and route the user's replies.'''
        self._render(self.engine.begin())

        while not self.engine.done:
            speech = read_user_input(self.use_voice)
            if speech is None:                       ## quit / Ctrl-C / Ctrl-D
                print("\nGoodbye.")
                return

            text = self.nlu.process(speech)
            option = self.nlu.select(text, self.engine.options())
            self._render(self.engine.submit(option))

    def _render(self, outputs):
        '''Speak utterances and print control lines as the engine emits them.'''
        for out in outputs:
            if out.say is not None:
                print("Robot:", self.nlg.process(out.say))
            elif out.control is not None:
                print("Robot: [continues in silence]")
            if out.control is not None:
                sock.sendto(struct.pack("<dd", 1, out.control), ("127.0.0.1", 5005))
                print(out.control)


QUIT_COMMANDS = ["quit", "exit"]


def read_user_input(use_voice=False):
    """Read one turn from the user. Returns None when the user wants to stop.

    In voice mode, pressing Enter (an empty line) is push-to-talk -- the mic is
    captured and transcribed downstream in NLU.ASR. Typing a reply instead still
    works as a manual override/fallback. In text mode the typed line is the reply.
    """
    prompt = "Press Enter to speak, or type a reply ('quit' to stop): " if use_voice else "You: "
    try:
        text = input(prompt).strip()
    except (EOFError, KeyboardInterrupt):

        ## user pressed ctrl+D or ctrl+C
        return None

    if text.lower() in QUIT_COMMANDS:
        return None

    return text


if __name__ == "__main__":
    if USE_VOICE:
        print("Voice mode: press Enter then speak, or type a response. Say/type 'quit' or press Ctrl+C to stop.")
    else:
        print("Press Enter to let the robot continue, or type a response. Type 'quit' or press Ctrl+C to stop.")
    Robot().run()
