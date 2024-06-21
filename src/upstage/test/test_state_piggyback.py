# Copyright (C) 2024 by the Georgia Tech Research Institute (GTRI)

# Licensed under the BSD 3-Clause License.
# See the LICENSE file in the project root for complete license terms and disclaimers.

import pytest

from upstage.actor import Actor
from upstage.api import Task, UpstageError, Wait
from upstage.base import EnvironmentContext
from upstage.states import LinearChangingState, State


class Piggy(Actor):
    a_level = LinearChangingState(recording=True)
    location = State()


class Rider(Actor):
    b_level = LinearChangingState(recording=True)
    location = State()
    piggy = State()


class RiderTask(Task):
    def task(self, *, actor: Actor):
        piggy = actor.piggy
        actor.activate_mimic_state(
            self_state="b_level",
            mimic_state="a_level",
            mimic_actor=piggy,
            task=self,
        )
        yield Wait(1.0)
        actor.deactivate_mimic_state(
            self_state="b_level",
            task=self,
        )


class RiderTaskTwo(Task):
    def task(self, *, actor: Actor):
        actor.activate_state(
            state="b_level",
            rate=2,
            task=self,
        )
        yield Wait(5.0)
        actor.deactivate_all_states(task=self)


def test_simple():
    with EnvironmentContext() as env:
        pig = Piggy(name="Piggy", a_level=1, location="here")
        ride = Rider(name="Rider", b_level=2, location="there", piggy=pig)

        assert ride.location == "there"
        ride.activate_mimic_state(
            self_state="location",
            mimic_state="location",
            mimic_actor=pig,
            task="None",
        )
        assert ride.location == "here"
        pig.location = "way over there"
        assert ride.location == "way over there"

        ride.deactivate_mimic_state(self_state="location", task="None")
        assert ride.location == "way over there"

        # a later test will check this differently
        assert not hasattr(ride, "_location_history")

        assert ride.b_level == 2
        ride.activate_mimic_state(
            self_state="b_level",
            mimic_state="a_level",
            mimic_actor=pig,
            task="None",
        )
        pig.activate_state(
            state="a_level",
            rate=2,
            task=None,
        )
        assert ride.b_level == 1
        env.run(until=4)

        pig.deactivate_all_states(task=None)

        assert ride.b_level == 9
        ride.deactivate_all_mimic_states(task="None")
        assert ride.b_level == 9

        ride.activate_state(
            state="b_level",
            rate=1,
            task=None,
        )
        env.run(until=5)
        assert ride.b_level == 10
        assert pig.a_level == 9


def test_rehearsing():
    with EnvironmentContext():
        pig = Piggy(name="Piggy", a_level=1, location="here")
        ride = Rider(name="Rider", b_level=2, location="there", piggy=pig)

        task = RiderTask()
        with pytest.raises(UpstageError):
            task.rehearse(actor=ride)


def test_rehearse_from_piggyback():
    with EnvironmentContext() as env:
        pig = Piggy(name="Piggy", a_level=1, location="here")
        ride = Rider(name="Rider", b_level=2, location="there", piggy=pig)

        assert ride.b_level == 2
        ride.activate_mimic_state(
            self_state="b_level",
            mimic_state="a_level",
            mimic_actor=pig,
            task="None",
        )
        pig.activate_state(
            state="a_level",
            rate=2,
            task=None,
        )
        assert ride.b_level == 1
        env.run(until=4)
        pig.deactivate_all_states(task=None)

        # Do not deactivate, instead call RiderTaskTwo
        # Pig went a_level to 9
        task = RiderTaskTwo()
        new_ride = task.rehearse(actor=ride)
        assert new_ride.b_level == 19
        assert ride.b_level == 9
        assert pig.a_level == 9

        ride.deactivate_mimic_state(self_state="b_level", task="None")
        pig.a_level = 12
        assert new_ride.b_level == 19
        assert ride.b_level == 9


def test_double_mimic():
    with EnvironmentContext():
        pig = Piggy(name="Piggy", a_level=1, location="here")
        ride = Rider(name="Rider", b_level=2, location="there", piggy=pig)

        ride.activate_mimic_state(
            self_state="b_level", mimic_state="a_level", mimic_actor=pig, task="None"
        )

        with pytest.raises(UpstageError):
            ride.activate_mimic_state(
                self_state="b_level",
                mimic_state="a_level",
                mimic_actor=pig,
                task="None",
            )


def test_interrupt_deactivate():
    with EnvironmentContext() as env:
        pig = Piggy(name="Piggy", a_level=1, location="here")
        ride = Rider(name="Rider", b_level=2, location="there", piggy=pig)

        ride.activate_mimic_state(
            self_state="b_level", mimic_state="a_level", mimic_actor=pig, task="None"
        )
        task = RiderTaskTwo()
        task.run(actor=ride)
        env.run()


def test_record():
    with EnvironmentContext():
        pig = Piggy(name="Piggy", a_level=1, location="here")

        class Rec(Actor):
            state = State(recording=True)

        class Rec2(Actor):
            state = State(recording=False)

        ride = Rec(
            name="another rider",
            state=3,
        )
        ride1 = Rec(
            name="another rider a",
            state=3,
        )
        ride2 = Rec2(
            name="another rider 2",
            state=3,
        )

        ride.activate_mimic_state(
            self_state="state",
            mimic_state="a_level",
            mimic_actor=pig,
            task="None",
        )

        ride1.activate_mimic_state(
            self_state="state",
            mimic_state="a_level",
            mimic_actor=pig,
            task="None",
        )

        ride2.activate_mimic_state(
            self_state="state",
            mimic_state="a_level",
            mimic_actor=pig,
            task="None",
        )

        pig.a_level = 23
        assert ride.state == 23
        assert ride1.state == 23
        assert ride2.state == 23
        assert hasattr(ride, "_state_history")
        assert hasattr(ride1, "_state_history")
        assert not hasattr(ride2, "_state_history")
        assert ride._state_history[1] == (0, 23)
        assert ride1._state_history[1] == (0, 23)
