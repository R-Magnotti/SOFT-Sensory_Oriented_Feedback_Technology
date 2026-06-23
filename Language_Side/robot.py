from NLU import NLU
from NLG import NLG
from deliberate import StoryEngine
from graph import StoryGraph
from context import DiscourseContext
import socket
import struct
import random

SCRIPT = "wound_cleaning.json"
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
while True:
    sock.sendto(struct.pack("<d", 5), ("127.0.0.1", 5006))
    print(5)

# class Robot:
#     def __init__(self, script=SCRIPT):
#         ## shared dialogue state, written by NLU
#         self.context = DiscourseContext()

#         ## NLP + dialogue modules. The engine walks the graph; the NLU matches
#         ## user replies to the branches the engine offers.
#         self.nlu = NLU(self.context)
#         self.nlg = NLG()
#         self.engine = StoryEngine(StoryGraph.from_file(script))

#     def run(self):
#         '''Drive the vignette: speak each beat, then read and route the user's replies.'''


#         self._render(self.engine.begin())

#         while not self.engine.done:
#             speech = read_user_input()
#             if speech is None:                       ## quit / Ctrl-C / Ctrl-D
#                 print("\nGoodbye.")
#                 return

#             text = self.nlu.process(speech)
#             option = self.nlu.select(text, self.engine.options())
#             self._render(self.engine.submit(option))

#     def _render(self, outputs):
#         '''Speak utterances and print control lines as the engine emits them.'''
#         for out in outputs:
#             if out.say is not None:
#                 print("Robot:", self.nlg.process(out.say))
#             elif out.control is not None:
#                 print("Robot: [continues in silence]")
#             if out.control is not None:
#                 print(out.control)
#                 sock.sendto(struct.pack("<d", out.control), ("127.0.0.1", 5005))

# QUIT_COMMANDS = ["quit", "exit"]


# def read_user_input():
#     """Read one line from the terminal. Returns None when the user wants to stop."""
#     try:
#         text = input("You: ").strip()
#     except (EOFError, KeyboardInterrupt):

#         ## user pressed ctrl+D or ctrl+C
#         return None

#     if text.lower() in QUIT_COMMANDS:
#         return None

#     return text


# if __name__ == "__main__":
#     print("Press Enter to let the robot continue, or type a response. Type 'quit' or press Ctrl+C to stop.")
#     sock.sendto(struct.pack("<d", 5), ("127.0.0.1", 5005))

#     Robot().run()
