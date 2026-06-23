class DiscourseContext:
    '''Shared dialogue state passed between NLP modules (history, turn count).'''
    def __init__(self):
        self.history = []
        self.turn = 0

    def add_utterance(self, utts):
        self.history.append(utts)
        self.turn += 1
