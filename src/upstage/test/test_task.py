# Copyright (C) 2024 by the Georgia Tech Research Institute (GTRI)

# Licensed under the BSD 3-Clause License.
# See the LICENSE file in the project root for complete license terms and disclaimers.

from inspect import isgeneratorfunction

import pytest
from simpy import Process

from upstage.actor import Actor
from upstage.api import SimulationError
from upstage.base import EnvironmentContext
from upstage.events import Wait
from upstage.states import LinearChangingState, State
from upstage.task import Task


class ActorForTest(Actor):
    dummy = State(recording=True)


class ActorChangeForTest(Actor):
    dummy = LinearChangingState()


class WorkingTask(Task):
    def task(self, *, actor):
        for wait_period in self.times:
            the_event = Wait(wait_period)
            yield the_event
            actor.dummy += wait_period


class ChangingTask(Task):
    def task(self, *, actor, times, rate):
        for t in times:
            the_event = Wait(t)
            actor.activate_state(state="dummy", task=self, rate=rate)
            yield the_event
            actor.deactivate_state(state="dummy", task=self)


class Actor2Test(Actor):
    dummy = State()


class WorkingTask2(Task):
    def task(self, *, actor):
        for wait_period in self.times:
            wait_event = Wait(wait_period)
            self.log.append(
                f"{self.env.now}: {self.__class__.__name__} "
                f"waiting {wait_period}, value={actor.dummy}"
            )
            yield wait_event
            self.log.append(
                f"{self.env.now}: {self.__class__.__name__} "
                f"finished waiting {wait_period}, "
                f"value={actor.dummy}"
            )
            actor.dummy += wait_period


class ChangingTask2(Task):
    def task(self, *, actor):
        for wait_period in self.times:
            wait_event = Wait(wait_period)
            actor.activate_state(state="dummy", task=self, rate=self.rate)
            actor.set_knowledge("example for logging", "a value", overwrite=True)
            self.log.append(
                f"{self.env.now}: {self.__class__.__name__} "
                f"waiting {wait_period}, value={actor.dummy}"
            )
            yield wait_event
            self.log.append(
                f"{self.env.now}: {self.__class__.__name__} finished "
                f"waiting {wait_period}, value={actor.dummy}"
            )
            actor.deactivate_state(state="dummy", task=self)


def _task_runner(env, rate, timeout_point):
    use_actor = ActorChangeForTest(name="testing", dummy=0, debug_log=True)
    times = [1, 2]

    task_object = ChangingTask2()
    task_object.times = times
    task_object.rate = rate
    task_object.log = []

    task_generator = task_object.run(
        actor=use_actor,
    )
    timeout = env.timeout(timeout_point)

    yield task_generator | timeout

    if task_generator.is_alive:
        task_generator.interrupt("cancelling")

    return use_actor


def test_creation() -> None:
    with EnvironmentContext():
        _ = WorkingTask()


def test_failures_for_tasks_with_simpy_events():
    with EnvironmentContext() as env:
        actor = ActorForTest(name="testing", dummy=0)

        class BrokenTask(Task):
            def task(self, *, actor):
                yield self.env.timeout(1.0)

        # msg = "*Task is yielding objects without `as_event`*"
        with pytest.raises(SimulationError):  # , match=msg):
            the_task = BrokenTask()
            _ = the_task.run(
                actor=actor,
            )
            env.run()

        # msg = "*'MockEnvironment' object has no attribute 'timeout'*"
        with pytest.raises(AttributeError):  # , match=msg):
            the_task = BrokenTask()
            the_task.rehearse(
                actor=actor,
            )


def test_failures_for_tasks_with_incorrect_events():
    with EnvironmentContext():
        actor = ActorForTest(name="testing", dummy=0)
        times = [1, 2]

        class BlankEvent:
            def __init__(self, **kwargs):
                pass

        class BrokenTask(Task):
            def task(self, *, actor, times, event_class):
                yield event_class()

        # msg = '*must be a subclass of BaseEvent*'
        with pytest.raises(SimulationError):
            task_instance = BrokenTask()
            task_instance.rehearse(
                actor=actor,
                times=times,
                event_class=BlankEvent,
            )


def test_running_as_rehearsal():
    with EnvironmentContext() as env:
        actor = ActorForTest(name="testing", dummy=0)
        times = [1, 2]
        task_object = WorkingTask()
        task_object.times = times
        rehearse_function = task_object.rehearse

        # assert that the task is not a generator
        msg = "Task when tested should not be a generator"
        assert not isgeneratorfunction(rehearse_function), msg

        result = rehearse_function(
            actor=actor,
        )
        msg = "Result of testing task must be an actor"
        assert isinstance(result, Actor), msg

        assert env.now == 0, "Environment time must not increase"

        msg = "Actor returned by task test is missing expected state changes"
        assert result.dummy == 3, msg

        msg = "Actor returned by task test needs to keep recorded data"
        assert len(result._dummy_history) == 3, msg
        assert result._dummy_history[0] == (0, 0), msg
        assert result._dummy_history[2] == (sum(times), sum(times)), msg

        msg = "No linkage between original actor and dummy actor"
        assert actor.dummy == 0, msg

        msg = "Environment not properly reset"
        assert task_object.env is env, msg


def test_running():
    with EnvironmentContext() as env:
        actor = ActorForTest(name="testing", dummy=0)
        times = [1, 2]

        task_object = WorkingTask()
        task_object.times = times
        task_process = task_object.run(
            actor=actor,
        )
        env.run()
        assert env.now == 3, "Environment time must increase"
        assert actor.dummy == 3, "Actor state must change"
        assert isinstance(
            task_process, Process
        ), "Task process is not an instance of simpy.Process"


def test_interrupting():
    with EnvironmentContext() as env:
        timeout_point = 0.5
        rate = 0.5
        proc = env.process(
            _task_runner(
                env,
                rate=rate,
                timeout_point=timeout_point,
            )
        )
        env.run()
        actor = proc.value
        msg = "Task interruption ended at the wrong time"
        assert actor.dummy == timeout_point * rate, msg


def test_interrupting_two():
    # Do the timeout right when a time will end
    with EnvironmentContext() as env:
        timeout_point = 1.0
        rate = 3.5
        proc = env.process(
            _task_runner(
                env=env,
                rate=rate,
                timeout_point=timeout_point,
            )
        )
        env.run()
        actor = proc.value
        msg = "Task interruption ended at the wrong time"
        assert actor.dummy == timeout_point * rate, msg


def test_simultaneous_task():
    with EnvironmentContext() as env:
        actor = ActorChangeForTest(name="testing", dummy=0)

        def task_runner(*, task_class, interrupt_time, **task_kwargs):
            task = task_class()
            task.log = []
            for k, v in task_kwargs.items():
                setattr(task, k, v)
            running_task = task.run(
                actor=actor,
            )

            timeout = env.timeout(interrupt_time)

            yield running_task | timeout

            if running_task.is_alive:
                running_task.interrupt("cancelling")

            return actor

        _ = env.process(
            task_runner(
                task_class=ChangingTask2,
                rate=1.0,
                times=[1.0, 3.0, 5.0, 6.0],
                interrupt_time=10.0,
            )
        )

        _ = env.process(
            task_runner(
                task_class=WorkingTask2,
                times=[2.0, 2.0, 2.0, 10.0],
                interrupt_time=12.0,
            )
        )

        env.run(until=20.0)


def test_terminal_task_run(task_objects: tuple[Task, Task, Actor]):
    EndPoint, EndPointBase, Dummy = task_objects

    with EnvironmentContext() as env:
        actor = Dummy(name="x", status="Good", debug_log=True)
        task = EndPoint()

        proc = task.run(actor=actor)
        env.run()
        assert env.now == 0

        assert "The Message" in actor._debug_log[-1]

        with pytest.raises(SimulationError, match=".+Cannot interrupt a terminal.+"):
            proc.interrupt()
            env.run()

        actor = Dummy(name="x", status="Good", debug_log=True)
        task = EndPointBase()
        proc = task.run(actor=actor)
        env.run()
        assert env.now == 0

        assert "Entering terminal task:" in actor._debug_log[-1]


def test_terminal_task_rehearse(task_objects: tuple[Task, Task, Actor]):
    EndPoint, _, Dummy = task_objects
    with EnvironmentContext():
        actor = Dummy(name="x", status="Good")
        task = EndPoint()

        clone = task.rehearse(actor=actor)
        assert clone.env.now == task._time_to_complete


class Restartable(Task):
    def task(self, *, actor: Actor):
        actor.activate_state(
            state="changer",
            task=self,
            rate=actor.rate,
        )
        self.set_marker("change to test")
        yield Wait(10.0)
        actor.deactivate_all_states(task=self)

    def on_interrupt(self, *, actor, cause):
        if cause == "restart":
            return self.INTERRUPT.RESTART
        else:
            return self.INTERRUPT.END


class Dummy(Actor):
    status = State()
    rate = State()
    changer = LinearChangingState(recording=True)


def test_restart():
    with EnvironmentContext() as env:
        actor = Dummy(
            name="Example",
            status="available",
            rate=2.3,
            changer=0.0,
            debug_log=True,
        )

        task = Restartable()
        proc = task.run(actor=actor)
        env.run(until=3.4)
        proc.interrupt(cause="restart")
        env.run()
        assert pytest.approx(actor.changer) == 2.3 * (3.4 + 10)