# Copyright (C) 2024 by the Georgia Tech Research Institute (GTRI)

# Licensed under the BSD 3-Clause License.
# See the LICENSE file in the project root for complete license terms and disclaimers.

import pytest
import simpy as SIM
from simpy.resources import base

from upstage.api import Actor, EnvironmentContext, SimulationError, State, Task
from upstage.events import (
    All,
    Any,
    BaseEvent,
    BaseRequestEvent,
    Event,
    Get,
    Put,
    ResourceHold,
    Wait,
)


def test_base_event():
    init_time = 1.23
    with EnvironmentContext(initial_time=init_time) as env:
        base = BaseEvent()
        assert (
            base.created_at == init_time
        ), "Problem in environment time being stored in event"
        assert base.env is env, "Problem in environment being stored in event"

        with pytest.raises(NotImplementedError):
            base.as_event()


def test_wait_event():
    init_time = 1.23
    with EnvironmentContext(initial_time=init_time) as env:
        timeout = 1

        wait = Wait(timeout=timeout)
        assert (
            wait.created_at == init_time
        ), "Problem in environment time being stored in event"
        assert wait.env is env, "Problem in environment being stored in event"
        assert wait.timeout == timeout

        ret = wait.as_event()
        assert isinstance(ret, SIM.Timeout), "Wait doesn't return a simpy timeout"
        assert ret._delay == timeout, "Incorrect timeout time"

    with EnvironmentContext(initial_time=init_time) as env:
        timeout = [1, 3]
        wait = Wait.from_random_uniform(*timeout)
        ret = wait.as_event()
        assert isinstance(ret, SIM.Timeout), "Wait doesn't return a simpy timeout"
        assert timeout[0] <= ret._delay <= timeout[1], "Incorrect timeout time"

        with pytest.raises(SimulationError):
            Wait(timeout={1, 2})

        with pytest.raises(SimulationError):
            Wait(timeout="1")

        with pytest.raises(SimulationError):
            Wait(timeout=[1])

        with pytest.raises(SimulationError):
            Wait(timeout=[1, 2, 3])


def test_base_request_event():
    init_time = 1.23
    with EnvironmentContext(initial_time=init_time) as env:
        base = BaseRequestEvent(env)
        assert (
            base.created_at == init_time
        ), "Problem in environment time being stored in event"
        assert base.env is env, "Problem in environment being stored in event"

        base.cancel()


def test_put_event_with_stores():
    with EnvironmentContext() as env:
        store = SIM.Store(env, capacity=1)
        put_object = ("A Test Object", 1.0)
        put_event = Put(store, put_object)

        assert (
            put_event.calculate_time_to_complete() == 0.0
        ), "Incorrect time to complete"
        returned_object = put_event.as_event()
        assert issubclass(
            returned_object.__class__, base.Put
        ), "Event returned is not simpy put event"
        env.run()
        assert returned_object.item is put_object, "Wrong object put"
        assert put_object in store.items

        put_object = ("A Second Test Object", 2.0)
        put_event = Put(store, put_object)
        event = put_event.as_event()
        env.run()
        assert not event.triggered, "Event shouldn't have completed"
        assert event in store.put_queue, "Event is not waiting"
        put_event.cancel()
        env.run()
        assert not event.triggered, "Event shouldn't have completed"
        assert event not in store.put_queue, "Event is still in the store's queue"


def test_put_event_with_containers():
    with EnvironmentContext() as env:
        container = SIM.Container(env, capacity=1)
        put_arg = 1.0
        put_event = Put(container, put_arg)

        assert (
            put_event.calculate_time_to_complete() == 0.0
        ), "Incorrect time to complete"
        returned_object = put_event.as_event()
        assert issubclass(
            returned_object.__class__, base.Put
        ), "Event returned is not simpy put event"
        env.run()
        assert returned_object.amount == put_arg, "Wrong amount put"
        assert container.level == put_arg

        put_arg = 2
        put_event = Put(container, put_arg)
        event = put_event.as_event()
        env.run()
        assert not event.triggered, "Event shouldn't have completed"
        assert event in container.put_queue, "Event is not waiting"
        put_event.cancel()
        env.run()
        assert not event.triggered, "Event shouldn't have completed"
        assert event not in container.put_queue, "Event is still in the store's queue"


def test_get_event_with_stores():
    with EnvironmentContext() as env:
        store = SIM.Store(env, capacity=1)
        put_object = ("A Test Object", 1.0)
        store.put(put_object)
        env.run()

        event = Get(store)
        assert event.calculate_time_to_complete() == 0.0, "Incorrect time to complete"
        returned_object = event.as_event()
        assert issubclass(
            returned_object.__class__, base.Get
        ), "Event returned is not simpy put event"

        env.run()
        item = event._request_event.value
        assert item is put_object, "Returned item is not the original item"
        item2 = event.get_value()
        assert item is item2, "Same object from both methods"

        event = Get(store)
        returned_object = event.as_event()
        env.run()
        assert returned_object in store.get_queue, "Event not in queue"
        event.cancel()
        assert returned_object not in store.get_queue, "Event is still in queue"


def test_get_event_with_containers():
    with EnvironmentContext() as env:
        container = SIM.Container(env, capacity=1)
        put_arg = 1.0
        container.put(put_arg)
        env.run()

        get_arg = 1.0
        event = Get(container, get_arg)
        assert event.calculate_time_to_complete() == 0.0, "Incorrect time to complete"
        returned_object = event.as_event()
        assert issubclass(
            returned_object.__class__, base.Get
        ), "Event returned is not simpy put event"

        env.run()
        amount = event._request_event.amount
        assert amount == get_arg, "Returned item is not the original item"
        with pytest.raises(
            SimulationError,
            match="'get_value' is not supported for Containers. "
            "Check is_complete and use the amount you "
            "requested",
        ):
            event.get_value()

        event = Get(container, get_arg)
        returned_object = event.as_event()
        env.run()
        assert returned_object in container.get_queue, "Event not in queue"
        event.cancel()
        assert returned_object not in container.get_queue, "Event is still in queue"


def test_resource_events():
    with EnvironmentContext() as env:
        a_resource = SIM.Resource(env, capacity=1)

        request_object = ResourceHold(a_resource)
        assert request_object._stage == "request", "Request object in wrong state"
        request_object.as_event()
        env.run()

        assert request_object._stage == "release", "Request object in wrong state"
        assert (
            a_resource.users[0] is request_object._request
        ), "The user is the request object"

        new_request = ResourceHold(a_resource)
        assert new_request._stage == "request", "Request object in wrong state"
        new_request.as_event()
        env.run()

        # TODO: A better name might be needed, since this request hasn't succeeded yet
        assert new_request._stage == "release", "Request object in wrong state"
        assert (
            not new_request._request.processed
        ), "Request went through when it shouldn't"

        # put the old one back
        request_object.as_event()
        env.run()
        assert new_request._request.processed, "Follow-on request didn't go through"

        newest_request = ResourceHold(a_resource)
        assert newest_request._stage == "request", "Request object in wrong state"
        newest_request.as_event()
        env.run()

        # cancel it
        assert newest_request._stage == "release", "Request object in wrong state"
        assert (
            not newest_request._request.processed
        ), "Request went through when it shouldn't"

        assert (
            newest_request._request in a_resource.put_queue
        ), "Resource isn't waiting to be gathered"
        with pytest.raises(SimulationError, match="Resource release requested.*?"):
            newest_request.as_event()

        newest_request.cancel()
        env.run()
        assert (
            newest_request._request not in a_resource.put_queue
        ), "Resource hasn't left the wait queue"


def test_multi_event():
    with EnvironmentContext() as env:
        event1 = Wait(1.0)
        event2 = Wait(1.5)
        event = All(event1, event2)
        assert event.calculate_time_to_complete() == 1.5

    with EnvironmentContext() as env:
        with pytest.warns(UserWarning):
            event1 = Wait(1.0)
            event2 = SIM.Timeout(env, 1.5)
            All(event1, event2)


def test_and_event():
    with EnvironmentContext() as env:

        def run(env, data):
            event1 = Wait(1.0)
            event2 = Wait(1.5)

            event = All(event1, event2)
            yield event.as_event()
            data["time"] = env.now
            data["events"] = [event1, event2]

        data = {}
        env.process(run(env, data))
        env.run()
        assert data["time"] == 1.5


def test_or_event():
    with EnvironmentContext() as env:

        def run(env, data):
            event1 = Wait(1.0)
            event2 = Wait(1.5)

            event = Any(event1, event2)
            yield event.as_event()
            data["time"] = env.now
            data["events"] = [event1, event2]

        data = {}
        env.process(run(env, data))
        env.run()
        # SimPy still runs the simulation long enough to finish the timeout
        assert data["time"] == 1.0


def test_composite():
    with EnvironmentContext() as env:

        def run(env, data):
            event1 = Wait(1.0)
            event2 = Wait(1.5)

            event3 = Wait(2.1)
            event4 = Wait(0.9)

            event_a = Any(event1, event2)
            event_b = All(event3, event4, event_a)
            result = yield event_b.as_event()
            data["time"] = env.now
            data["result"] = result

        data = {}
        env.process(run(env, data))
        env.run()
        assert data["time"] == 2.1
        assert len(data["result"].events) == 4


def test_process_in_multi():
    with EnvironmentContext() as env:

        def a_process():
            yield env.timeout(2)

        class Thing(Actor):
            result = State()
            events = State()

        class TheTask(Task):
            def task(self, *, actor):
                wait = Wait(3.0)
                proc = env.process(a_process())
                res = yield Any(wait, proc)
                actor.events = [wait, proc]
                actor.result = res

        t = Thing(name="Thing", result=None, events=None)
        task = TheTask()
        task.run(actor=t)
        with pytest.warns(UserWarning):
            env.run()
        assert t.events[-1] in t.result
        assert t.events[0] not in t.result


def test_rehearse_process_in_multi():
    with EnvironmentContext() as env:

        def a_process():
            yield env.timeout(2)

        class Thing(Actor):
            result = State()
            events = State()

        class TheTask(Task):
            def task(self, *, actor):
                wait = Wait(3.0)
                proc = env.process(a_process())
                res = yield Any(wait, proc)
                actor.events = [wait, proc]
                actor.result = res

        t = Thing(name="Thing", result=None, events=None)
        task = TheTask()
        with pytest.raises(SimulationError, match="All events in a MultiEvent"):
            with pytest.warns(UserWarning):
                task.rehearse(actor=t)


# # TODO: Test how to retrieve event items


def test_basic_usage():
    with EnvironmentContext() as env:
        event = Event()
        assert event._event is not None
        assert isinstance(event._event, SIM.Event)
        assert event._event is event.as_event()
        assert event.is_complete() is False

        def run_one(env, event):
            yield env.timeout(1.0)
            event.succeed(data="here")

        def run_two(env, event, data):
            yield event._event
            data["time"] = env.now

        env.process(run_one(env, event))
        data = {}
        env.process(run_two(env, event, data))
        env.run()
        assert data["time"] == 1.0
        assert event.is_complete()
        payload = event.get_payload()
        assert payload == {"data": "here"}

        with pytest.raises(SimulationError):
            event.succeed()

        assert event.calculate_time_to_complete() == 0.0

        last_event = event._event
        event.reset()
        assert last_event is not event._event


def test_conflicts():
    with EnvironmentContext() as env:
        event = Event()

        def run_one(env, event):
            yield env.timeout(1.0)
            event.succeed()

        def run_two(env, event, data):
            yield event._event
            data["time_two"] = env.now

        def run_three(env, event, data):
            yield event._event
            data["time_three"] = env.now

        def run_four(env, event):
            yield env.timeout(1.1)
            event.succeed()

        env.process(run_one(env, event))
        data = {}
        env.process(run_two(env, event, data))
        env.process(run_three(env, event, data))
        env.run()
        assert data["time_two"] == data["time_three"]

    with EnvironmentContext() as env:
        with pytest.raises(SimulationError):
            event = Event()
            env.process(run_one(env, event))
            data = {}
            env.process(run_two(env, event, data))
            env.process(run_three(env, event, data))
            env.process(run_four(env, event))
            env.run()

    with EnvironmentContext() as env:

        def run_four_alt(env, event):
            yield env.timeout(1.1)
            event.succeed()

        def run_five(env, event, data):
            # Timeout until after the event suceeded, but before its reset
            yield env.timeout(1.05)
            yield event.as_event()
            data["time_five"] = env.now

        event = Event()
        env.process(run_one(env, event))
        data = {}
        env.process(run_two(env, event, data))
        env.process(run_three(env, event, data))
        env.process(run_four_alt(env, event))
        env.process(run_five(env, event, data))
        env.run()
        assert data["time_two"] == data["time_three"]
        assert data["time_five"] == 1.1
