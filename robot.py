from NLU import NLU
from NLG import NLG
from deliberate import deliberate
from context import DiscourseContext

class Robot:
    def __init__(self):
        ## shared dialogue state, written by NLU and read by deliberate
        self.context = DiscourseContext()

        ## initialize NLP robot control modules
        self.nlu_module = NLU(self.context)
        self.deliberate_module = deliberate(self.context)
        self.nlg_module = NLG()

    def greet(self):
        ## turn 0: robot speaks first, before any user input
        intro = self.deliberate_module.greeting()
        print("Robot:", self.nlg_module.process(intro))

    def run(self, user_speech):
        processed_text = self.nlu_module.process(user_speech)
        result = self.deliberate_module.process(processed_text)

        if result['say'] is not None:
            print("Robot:", self.nlg_module.process(result['say']))
        elif result['control'] is not None:
            print("Robot: [continues in silence]")

        if result['control'] is not None:
            print(result['control'])

        return result['end']


QUIT_COMMANDS = ["quit", "exit"]

def read_user_input():
    """Read one line from the terminal. Returns None when the user wants to stop."""
    try:
        text = input("You: ").strip()
    except (EOFError, KeyboardInterrupt):
        
        ## user pressed ctrl+D or ctrl+C
        return None

    if text.lower() in QUIT_COMMANDS:
        return None

    return text

if __name__ == "__main__":
    my_robot = Robot()
    my_robot.greet()
    print("Press Enter to let the robot continue, or type a response. Type 'quit' or press Ctrl+C to stop.")

    while True:
        user_speech = read_user_input()

        if user_speech is None:
            print("\nGoodbye.")
            break

        if my_robot.run(user_speech):
            break