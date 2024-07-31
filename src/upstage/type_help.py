from collections.abc import Generator
from typing import Any
from upstage.events import BaseEvent
from simpy import Event as SimEvent


TASK_GEN = Generator[BaseEvent, Any, None]
SIMPY_GEN = Generator[SimEvent, Any, None]
