class NLU:
    '''NLU module to do ASR, and track relevant discourse information'''
    def __init__(self, context):
        self.context = context

    def process(self, speech):
        '''
        Goal: pass user speech input through NL pipeline
        '''
        utterances = self.ASR(speech)
        self.update_LF(utterances)
        
        return utterances

    ## speech audio will be hardcoded for now
    def ASR(self, speech):
        '''
        Params: 
            speech: human's utterances
        Goal: convert audio utterances to text (using off the shelf ASR tool)
        '''
        return speech
        
    def update_LF(self, utts:str):
        '''
        Goal: use most recent utterances to update relevant discourse information
        '''
        self.context.add_utterance(utts)

