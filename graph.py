"""
Data model for the narrative vignette.

The story is a directed graph (cycles allowed) of dialogue states, loaded from
JSON (see wound_cleaning.json). Keeping the structure declarative means the
procedure can be authored, reviewed, or swapped without touching the engine
that walks it (deliberate.py).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterator, Optional


@dataclass(frozen=True)
class Option:
    """One branch out of an input state: user text matching any of `utterances`
    moves the story to state `to`. `intent` is a human-readable label."""
    intent: str
    utterances: tuple[str, ...]
    to: str


@dataclass(frozen=True)
class Control:
    """A physical action the robot performs on entering a state."""
    action: str          # e.g. "DAB"
    ease: int = 0        # lower the current dab force by this many % before acting


@dataclass(frozen=True)
class State:
    """A single beat of the vignette. Exactly one transition style applies:

      * `auto_to` set    -> no reply needed; advance to it after `pause` seconds.
      * `options` set    -> wait for user text, branch on the matched Option.
      * `terminal`       -> the story ends here.

    A state with neither options nor auto (only a `fallback`) still waits for
    input, but accepts any reply and advances to `fallback` (e.g. the greeting,
    which records a rating without branching on it).
    """
    id: str
    say: Optional[str] = None
    control: Optional[Control] = None
    auto_to: Optional[str] = None
    pause: float = 2.0
    options: tuple[Option, ...] = ()
    fallback: Optional[str] = None       # taken when no option matches (incl. empty input)
    terminal: bool = False

    @property
    def waits_for_input(self) -> bool:
        return not self.terminal and self.auto_to is None

    def targets(self) -> Iterator[str]:
        """Every state id this state can transition to (for validation)."""
        if self.auto_to:
            yield self.auto_to
        for opt in self.options:
            yield opt.to
        if self.fallback:
            yield self.fallback


@dataclass(frozen=True)
class StoryGraph:
    start: str
    states: dict[str, State]
    global_options: tuple[Option, ...] = ()   # branches offered at every input state

    def __getitem__(self, state_id: str) -> State:
        return self.states[state_id]

    @classmethod
    def from_file(cls, path: str) -> "StoryGraph":
        with open(path, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

    @classmethod
    def from_dict(cls, data: dict) -> "StoryGraph":
        states = {sid: _state(sid, spec) for sid, spec in data["states"].items()}
        global_options = tuple(_option(o) for o in data.get("global", {}).get("options", []))
        graph = cls(start=data["start"], states=states, global_options=global_options)
        graph.validate()
        return graph

    def validate(self) -> None:
        """Fail fast on dangling transitions so authoring mistakes surface at load."""
        ids = set(self.states)
        referenced = {self.start}
        for state in self.states.values():
            referenced.update(state.targets())
        referenced.update(opt.to for opt in self.global_options)
        missing = referenced - ids
        if missing:
            raise ValueError(f"graph references unknown states: {sorted(missing)}")


# --- JSON -> dataclass helpers ---------------------------------------------------

def _option(spec: dict) -> Option:
    return Option(intent=spec.get("intent", ""), utterances=tuple(spec["utterances"]), to=spec["to"])


def _control(spec: Optional[dict]) -> Optional[Control]:
    if not spec:
        return None
    return Control(action=spec["action"], ease=int(spec.get("ease", 0)))


def _state(state_id: str, spec: dict) -> State:
    auto = spec.get("auto") or {}
    return State(
        id=state_id,
        say=spec.get("say"),
        control=_control(spec.get("control")),
        auto_to=auto.get("to"),
        pause=float(auto.get("after", 2.0)),
        options=tuple(_option(o) for o in spec.get("options", [])),
        fallback=spec.get("fallback"),
        terminal=bool(spec.get("terminal", False)),
    )
