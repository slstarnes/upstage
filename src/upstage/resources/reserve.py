# Copyright (C) 2024 by the Georgia Tech Research Institute (GTRI)

# Licensed under the BSD 3-Clause License.
# See the LICENSE file in the project root for complete license terms and disclaimers.

from ..task import process
from simpy import Environment, Event
from typing import Any, Generator


__all__ = ("ReserveStore",)


class ReserveStore:
    """A store that allows requests to be scheduled in advance.

    This is not a true store (you can't yield on a reserve slot!).

    :param env: simpy environment
    :param capacity: capacity of the store

    :type env: :class:`simpy.Environment`
    :type capacity: int

    """

    def __init__(
        self, env: Environment, init: float = 0.0, capacity: float = float("inf")
    ) -> None:
        self.capacity = capacity
        self._env = env
        self._level = init
        self._real_level = init
        self._queued: dict[Any, tuple[float, float]] = {}

    @property
    def remaining(self) -> float:
        return self._level

    @property
    def available(self) -> float:
        return self.remaining

    @property
    def queued(self) -> list[Any]:
        return list(self._queued.keys())

    @process
    def _expire_request(
        self, requester: Any, time: float
    ) -> Generator[Event, None, None]:
        """Expire the request after an expiration period or at a specific time.

        :param request: the Request namedtuple object
        :param expiration: the expiration Event object

        :type request:
        :type expiration:

        """
        yield self._env.timeout(time)
        self.cancel_request(requester)

    def reserve(
        self, requester: Any, quantity: float, expiration: float | None = None
    ) -> bool:
        """Reserve a quantity of storage."""
        if self.available < quantity:
            return False
        elif requester not in self._queued:
            self._level -= quantity
            self._queued[requester] = (quantity, self._env.now)
            if expiration is not None:
                self._expire_request(requester, expiration)
            return True
        else:
            return False

    def cancel_request(self, requester: Any) -> bool:
        """Have a request cancelled."""
        if requester not in self._queued:
            return False
        else:
            request = [x for x in self._queued if x is requester]
            if not request:
                raise ValueError("Requester not available to cancel")
            self._level += self._queued[requester][0]
            self._queued.pop(request[0])
            return True

    def take(self, requester: Any) -> float:
        """If in queue, allow requester take the actual quantity."""
        if requester not in self._queued:
            raise ValueError("Requester is not in queue, cannot take.")
        else:
            amt, _ = self._queued.pop(requester)
            self._real_level -= amt
            return amt

    def put(self, amount: float, capacity_increase: bool = False) -> None:
        """Put some quantity back in."""
        new = self._level + amount
        if new > self.capacity and not capacity_increase:
            raise ValueError("Adding too much.")
        else:
            self._level = new
            self._real_level += amount
