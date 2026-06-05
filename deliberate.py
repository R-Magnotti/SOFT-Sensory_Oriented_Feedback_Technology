"""
Graph-driven deliberation engine.

`StoryEngine` walks the narrative-vignette graph (graph.py / wound_cleaning.json):
it emits each state's speech and robot control, follows automatic transitions
after a short pause, and stops at branch points to wait for user input. It never
inspects raw user text -- branch selection is delegated to the NLU matcher and
handed back via `submit()`, so understanding and dialogue control stay separate.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Iterator, List, Optional

from graph import Option, State, StoryGraph


@dataclass(frozen=True)
class Output:
    """What the robot does on entering a state: an utterance and/or a control
    command. `say` is None for naturalistic silence."""
    say: Optional[str]
    control: Optional[str]


class StoryEngine:
    def __init__(
        self,
        graph: StoryGraph,
        *,
        base_force: int = 50,
        min_force: int = 10,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.graph = graph
        self.force = base_force          # current dab force (%); lowered on a pain signal
        self.min_force = min_force       # floor: force never reaches 0 (robot stays in contact)
        self._sleep = sleep              # injectable so tests can skip the real pauses
        self.current = graph.start
        self.done = False

    def begin(self) -> Iterator[Output]:
        """Emit the opening state and run until input is needed or the story ends."""
        yield from self._drive_from(self.current)

    def options(self) -> List[Option]:
        """Branches available at the current input state (state-local + global)."""
        return list(self.graph[self.current].options) + list(self.graph.global_options)

    def submit(self, option: Optional[Option]) -> Iterator[Output]:
        """Leave the current input state. `option` is the matched branch, or None
        to take the state's fallback (an unmatched or empty reply)."""
        state = self.graph[self.current]
        target = option.to if option else (state.fallback or state.id)
        yield from self._drive_from(target)

    def _drive_from(self, state_id: str) -> Iterator[Output]:
        """Enter `state_id`, then keep following automatic transitions -- pausing
        between them -- until a state needs input or ends the story. Yielding as
        it goes lets the caller render each beat with its pause felt in real time."""
        self.current = state_id
        while True:
            state = self.graph[self.current]
            yield self._enter(state)
            if state.terminal:
                self.done = True
                return
            if state.waits_for_input:
                return
            self._sleep(state.pause)
            self.current = state.auto_to

    def _enter(self, state: State) -> Output:
        """Apply a state's side effects (force easing) and render its control line."""
        control = None
        if state.control:
            if state.control.ease:
                self.force = max(self.min_force, self.force - state.control.ease)
            control = f"[control] action={state.control.action} force={self.force}%"
        return Output(say=state.say, control=control)
