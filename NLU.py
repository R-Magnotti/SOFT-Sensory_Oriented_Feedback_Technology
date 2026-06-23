from typing import Optional, Sequence, TypeVar

from matchers import FuzzyMatcher, HasUtterances, UtteranceMatcher

## an option is anything exposing representative `.utterances` (e.g. graph.Option)
Opt = TypeVar("Opt", bound=HasUtterances)


class NLU:
    '''NLU module: ASR, discourse tracking, and matching user text to dialogue options.'''
    def __init__(self, context, matcher: Optional[UtteranceMatcher] = None):
        self.context = context
        ## the matcher is a swappable strategy: fuzzy today, an LM/classifier later
        self.matcher = matcher or FuzzyMatcher()

    def process(self, speech):
        '''
        Goal: pass user speech input through the NL pipeline; returns recognised text.
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
