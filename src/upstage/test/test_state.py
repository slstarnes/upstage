# Copyright (C) 2024 by the Georgia Tech Research Institute (GTRI)

# Licensed under the BSD 3-Clause License.
# See the LICENSE file in the project root for complete license terms and disclaimers.

import pytest
from simpy import Container, Store

import upstage.api as UP
import upstage.resources.monitoring as monitor
from upstage.actor import Actor
from upstage.api import EnvironmentContext, SimulationError, UpstageError
from upstage.states import LinearChangingState, ResourceState, State


class StateTest:
    state_one = State()
    state_two = State(recording=True)
    lister = State(default=[])
    diction = State(default={})
    setstate = State(default=set())

    def __init__(self, env):
        self.env = env
        # including for compatibility
        self._mimic_states = {}
        self._state_listener = None

    def set_one(self, val):
        self.state_one = val

    def set_two(self, val):
        self.state_two = val


class StateTestActor(Actor):
    state_one = State()
    state_two = State(recording=True)
    state_three = LinearChangingState(recording=True)


def test_state_fails_without_env() -> None:
    """Test that recording states need the class to have an env attribute"""
    tester = StateTest(None)
    # the first one should not raise an error
    tester.set_one(1)

    with pytest.raises(SimulationError):
        tester.set_two(1)


def test_state_values() -> None:
    """Test that we get the right state values we input"""
    with EnvironmentContext(initial_time=1.5) as env:
        tester = StateTest(env)
        tester.state_one = 1
        assert tester.state_one == 1
        tester.state_two = 2
        assert tester.state_two == 2


def test_state_recording() -> None:
    with EnvironmentContext(initial_time=1.5) as env:
        tester = StateTest(env)
        tester.state_two = 2
        assert hasattr(tester, "_state_two_history")
        env.run(until=2.5)
        tester.state_two = 3
        assert len(tester._state_two_history) == 2
        assert tester._state_two_history[0] == (1.5, 2)
        assert tester._state_two_history[1] == (2.5, 3)


def test_state_mutable_default() -> None:
    with EnvironmentContext(initial_time=1.5) as env:
        tester = StateTest(env)
        tester2 = StateTest(env)
        assert id(tester.lister) != id(tester2.lister)
        tester.lister.append(1)
        assert len(tester2.lister) == 0
        assert len(tester.lister) == 1

        assert id(tester.diction) != id(tester2.diction)
        tester2.diction[1] = 2
        assert len(tester.diction) == 0
        assert len(tester2.diction) == 1

        assert id(tester.setstate) != id(tester2.setstate)
        tester2.setstate.add(1)
        assert len(tester.setstate) == 0
        assert len(tester2.setstate) == 1


def test_state_values_from_init() -> None:
    with EnvironmentContext() as env:
        tester = StateTestActor(
            name="testing",
            state_one=1,
            state_two=2,
            state_three=4,
        )
        env.run(until=1.5)
        assert tester.state_one == 1
        assert tester.state_two == 2
        assert tester.state_three == 4
        tester.state_three = 3
        assert hasattr(tester, "_state_three_history")
        assert tester._state_three_history == [(0.0, 4), (1.5, 3)]


def test_linear_changing_state() -> None:
    state_three_init = 3
    init_time = 1.5
    rate = 3.1
    timestep = 1

    with EnvironmentContext(initial_time=init_time) as env:
        tester = StateTestActor(
            name="testing",
            state_one=1,
            state_two=2,
            state_three=state_three_init,
        )

        task = "SomeTask"

        tester.activate_state(state="state_three", task=task, rate=rate)
        assert "state_three" in tester._active_states
        assert tester._active_states["state_three"] == tester.get_active_state_data(
            "state_three", without_update=True
        )
        env.run(until=init_time + timestep)
        # Test getting the value before it's ended
        assert tester.state_three == rate * timestep + state_three_init
        env.run(until=init_time + timestep * 2)
        state_data = tester.get_active_state_data("state_three", without_update=True)
        assert state_data["started_at"] == timestep + init_time
        assert state_data["rate"] == rate
        tester.deactivate_state(state="state_three", task=task)
        assert "state_three" not in tester._active_states
        assert tester.state_three == rate * timestep * 2 + state_three_init


def test_resource_state_valid_types() -> None:
    class Holder(Actor):
        res = ResourceState(valid_types=Store)

    with EnvironmentContext():
        Holder(
            name="example",
            res={"kind": Store},
        )

        with pytest.raises(UpstageError):
            Holder(
                name="example",
                res={"kind": Container},
            )

        with pytest.raises(UpstageError):

            class _(Actor):
                res = ResourceState(valid_types=(1,))

        with pytest.raises(UpstageError):

            class _(Actor):
                res = ResourceState(valid_types=(Actor,))


def test_resource_state_set_protection() -> None:
    class Holder(Actor):
        res = ResourceState(valid_types=(Store))

    with EnvironmentContext():
        h = Holder(
            name="example",
            res={"kind": Store},
        )
        with pytest.raises(UpstageError, match=".+It cannot be changed once set.+"):
            h.res = 1.0


def test_resource_state_no_default_init() -> None:
    class Holder(Actor):
        res = ResourceState()

    with EnvironmentContext():
        with pytest.raises(UpstageError, match="Missing values for states"):
            h = Holder(
                name="example",
            )

        with pytest.raises(UpstageError, match="No resource type"):
            h = Holder(
                name="example",
                res={},
            )

        h = Holder(
            name="example",
            res={"kind": Store},
        )
        assert isinstance(h.res, Store)


def test_resource_state_default_init() -> None:
    class Holder(Actor):
        res = ResourceState(default=Store)

    with EnvironmentContext():
        h = Holder(name="Example")
        assert isinstance(h.res, Store)

        h = Holder(name="Example", res={"capacity": 10})
        assert isinstance(h.res, Store)
        assert h.res.capacity == 10


def test_resource_state_kind_init() -> None:
    class Holder(Actor):
        res = ResourceState()

    with EnvironmentContext():
        h = Holder(name="Example", res={"kind": Store, "capacity": 10})
        assert isinstance(h.res, Store)
        assert h.res.capacity == 10

        h = Holder(name="Example", res={"kind": Container, "capacity": 100, "init": 50})
        assert isinstance(h.res, Container)
        assert h.res.capacity == 100
        assert h.res.level == 50

        test_resources = [
            x
            for x in monitor.__dict__.values()
            if isinstance(x, type) and issubclass(x, Store | Container)
        ]
        for the_class in test_resources:
            h = Holder(name="Example", res={"kind": the_class, "capacity": 99})
            assert isinstance(h.res, the_class)
            assert h.res.capacity == 99


def test_resource_state_simpy_store_running() -> None:
    class Holder(Actor):
        res = ResourceState()

    with EnvironmentContext() as env:
        h = Holder(name="Example", res={"kind": Store, "capacity": 10})

        def put_process(entity):
            for i in range(11):
                yield env.timeout(1.0)
                yield entity.res.put(f"Item {i}")
            return "Done"

        def get_process(entity):
            res = yield entity.res.get()
            return res

        proc_1 = env.process(put_process(h))
        proc_2 = env.process(get_process(h))
        env.run()
        assert proc_2.value == "Item 0"
        assert proc_1.value == "Done"


def test_resource_clone() -> None:
    class Holder(Actor):
        res = ResourceState(default=Store)

    with EnvironmentContext():
        holder = Holder(name="example")
        holder_2 = holder.clone()
        assert id(holder_2.res.items) != id(holder.res.items)

        class Holder(Actor):
            res = ResourceState(default=Container)

        holder = Holder(name="example")
        holder_2 = holder.clone()
        assert id(holder_2.res.level) != id(holder.res.level)


class HelperCallback:
    def __init__(self):
        self.cbacks = []

    def _callbacker(self, instance, value):
        self.cbacks.append((instance, value))


def test_state_callback() -> None:
    class CbackActor(Actor):
        state_one = State(recording=True)

    helper = HelperCallback()
    with EnvironmentContext():
        actor = CbackActor(
            name="Test",
            state_one=1,
        )

        actor._add_callback_to_state("source", helper._callbacker, "state_one")
        actor.state_one = 2
        assert len(helper.cbacks) == 1
        assert helper.cbacks[0][1] == 2
        actor._remove_callback_from_state("source", "state_one")

        actor.state_one = 3
        assert len(helper.cbacks) == 1


def test_matching_states() -> None:
    """Test the state matching code.
    At this time, state matching only works with CommunicationStore. It's the
    only state with a special attribute attached to it.
    """

    class Worker(UP.Actor):
        sleepiness = UP.State(default=0, valid_types=(float,))
        walkie = UP.CommunicationStore(mode="UHF")
        intercom = UP.CommunicationStore(mode="loudspeaker")

    with EnvironmentContext():
        worker = Worker(name="Billy")
        store_name = worker._get_matching_state(
            UP.CommunicationStore,
            {"_mode": "loudspeaker"},
        )
        store = getattr(worker, store_name)
        assert store is worker.intercom, "Wrong state retrieved"
        assert store is not worker.walkie, "Wrong state retrieved"

        # Show the FCFS behavior
        state_name = worker._get_matching_state(
            UP.State,
        )
        value = getattr(worker, state_name)
        assert value == worker.sleepiness, "Wrong state retrieved"

        # Show the FCFS behavior with state type
        state_name = worker._get_matching_state(
            UP.CommunicationStore,
        )
        value = getattr(worker, state_name)
        assert value is worker.walkie, "Wrong state retrieved"
