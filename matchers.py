"""
Pluggable utterance matching for the NLU layer.

`UtteranceMatcher` is the seam. Today the only implementation is `FuzzyMatcher`
(dependency-free string similarity), but anything that maps user text to the
closest candidate phrase can be dropped in -- an embedding lookup, an intent
classifier, a small language model -- by subclassing `UtteranceMatcher` and
passing the instance to `NLU(..., matcher=...)`. Nothing else has to change.
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Optional, Protocol, Sequence, runtime_checkable


@runtime_checkable
class HasUtterances(Protocol):
    """Anything carrying example phrasings to compare against (e.g. graph.Option)."""
    utterances: Sequence[str]


@dataclass(frozen=True)
class MatchResult:
    """The winning candidate phrase (or None if nothing cleared the bar) and its score."""
    candidate: Optional[str]
    score: float


class UtteranceMatcher(ABC):
    """Strategy: pick the candidate phrase closest to the user's text."""

    @abstractmethod
    def match(self, text: str, candidates: Sequence[str]) -> MatchResult:
        ...


class FuzzyMatcher(UtteranceMatcher):
    """Dependency-free baseline matcher.

    Each candidate is scored by the larger of (a) character-level similarity and
    (b) token-overlap F1, so short commands like "yes" or "stop" still match
    inside a longer sentence ("yes, go ahead") without a bare candidate word
    falsely matching a phrase that merely contains it ("ready" vs "not ready").
    The best candidate wins, or no match when its score is below `threshold`.
    """

    _WORD = re.compile(r"[a-z0-9']+")

    def __init__(self, threshold: float = 0.6):
        self.threshold = threshold

    def match(self, text: str, candidates: Sequence[str]) -> MatchResult:
        best, best_score = None, 0.0
        for candidate in candidates:
            score = self._score(text, candidate)
            if score > best_score:
                best, best_score = candidate, score
        if best_score < self.threshold:
            return MatchResult(None, best_score)
        return MatchResult(best, best_score)

    def _score(self, text: str, candidate: str) -> float:
        t, c = text.lower().strip(), candidate.lower().strip()
        if not t or not c:
            return 0.0
        ratio = SequenceMatcher(None, t, c).ratio()
        return max(ratio, self._token_f1(t, c))

    def _token_f1(self, text: str, candidate: str) -> float:
        """F1 of shared tokens: rewards covering the candidate (recall) while
        penalising candidates that explain little of the user's words (precision)."""
        t_tokens, c_tokens = set(self._WORD.findall(text)), set(self._WORD.findall(candidate))
        if not t_tokens or not c_tokens:
            return 0.0
        shared = len(t_tokens & c_tokens)
        if not shared:
            return 0.0
        precision, recall = shared / len(t_tokens), shared / len(c_tokens)
        return 2 * precision * recall / (precision + recall)
