from NLU import NLU
from NLG import NLG
from deliberate import StoryEngine
from graph import StoryGraph
from context import DiscourseContext
import argparse
import os
import socket
import struct

SCRIPT = "wound_cleaning.json"

## A single switch controls all voice I/O -- mic speech-to-text (ASR) AND spoken
## text-to-speech (TTS) together. It defaults on, seeded from SOFT_VOICE for
## backward compatibility, and is overridable per run with --voice / --no-voice.
DEFAULT_VOICE = os.environ.get("SOFT_VOICE", "1") != "0"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(struct.pack("<dd", 1, 0), ("127.0.0.1", 5005))

class Robot:
    def __init__(self, script=SCRIPT, use_voice=DEFAULT_VOICE):
        ## shared dialogue state, written by NLU
        self.context = DiscourseContext()

        ## NLP + dialogue modules. The engine walks the graph; the NLU matches
        ## user replies to the branches the engine offers. The same use_voice
        ## switch drives the NLU's mic ASR and the NLG's spoken TTS.
        self.nlu = NLU(self.context, use_voice=use_voice)
        self.nlg = NLG(use_voice=use_voice)
        self.engine = StoryEngine(StoryGraph.from_file(script))
        ## reflect what the NLU actually enabled (it may have fallen back to text)
        self.use_voice = self.nlu.use_voice

    def run(self):
        '''Drive the vignette: speak each beat, then read and route the user's replies.'''
        self._render(self.engine.begin())

        while not self.engine.done:
            ## Pausing for the user: drop the signal to 0 so the robot holds
            ## a neutral/resting state while it waits for a reply.
            self._send_control(0)
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
                self._send_control(out.control)
                print(out.control)

    def _send_control(self, value):
        '''Emit a control signal to the robot driver over UDP.'''
        sock.sendto(struct.pack("<dd", 1, value), ("127.0.0.1", 5005))


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


def parse_args():
    '''The one binary switch for voice I/O: --voice / --no-voice toggles mic ASR
    and spoken TTS together (default seeded from SOFT_VOICE, on unless set to 0).'''
    parser = argparse.ArgumentParser(description="Run the SOFT wound-cleaning vignette.")
    parser.add_argument(
        "--voice", action=argparse.BooleanOptionalAction, default=DEFAULT_VOICE,
        help="Enable voice I/O -- mic speech-to-text and spoken text-to-speech "
             "together. Use --no-voice for a silent type-only run (default: on).")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.voice:
        print("Voice mode: press Enter then speak, or type a response. Say/type 'quit' or press Ctrl+C to stop.")
    else:
        print("Press Enter to let the robot continue, or type a response. Type 'quit' or press Ctrl+C to stop.")
    Robot(use_voice=args.voice).run()
