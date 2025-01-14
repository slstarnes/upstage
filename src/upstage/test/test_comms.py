# Copyright (C) 2024 by the Georgia Tech Research Institute (GTRI)

# Licensed under the BSD 3-Clause License.
# See the LICENSE file in the project root for complete license terms and disclaimers.

from simpy import Store

import upstage.api as UP
from upstage.api import (
    CommsManager,
    EnvironmentContext,
    Get,
    Message,
    MessageContent,
    Task,
    UpstageBase,
    Wait,
)
from upstage.communications.processes import generate_comms_wait


class ReceiveSend(UpstageBase):
    # A mock 'actor' to do the tasks of either sending or receiving
    def __init__(self):
        super().__init__()
        self.incoming = Store(env=self.env)
        self.result = None


class ReceiveTask(Task):
    def task(self, *, actor):
        item = yield Get(actor.incoming)
        actor.result = item


class SendTask(Task):
    def task(self, *, actor):
        yield Wait(1.0)
        content = MessageContent(data=dict(action="move", thought="good"))
        message = Message(actor, content, self.receiver)
        yield self.comms.make_put(message, actor, self.receiver)


def test_send_receive():
    with EnvironmentContext() as env:
        receiver = ReceiveSend()
        sender = ReceiveSend()

        rec_task = ReceiveTask()
        sen_task = SendTask()

        comms = CommsManager(
            name="Comm",
            init_entities=[(receiver, "incoming")],
            debug_logging=True,
        )
        comms.run()

        rec_task.run(actor=receiver)
        sen_task.comms = comms
        sen_task.receiver = receiver
        sen_task.run(actor=sender)

        env.run()

        assert env.now == 1.0, "Wrong simulation end time for comms"
        assert receiver.result is not None, "No result for comms"
        assert isinstance(receiver.result, Message), "Wrong result format"
        content = receiver.result.content.data
        assert content["action"] == "move"
        assert content["thought"] == "good"


def test_send_receive_delayed():
    with EnvironmentContext() as env:
        receiver = ReceiveSend()
        sender = ReceiveSend()

        rec_task = ReceiveTask()
        sen_task = SendTask()

        comms = CommsManager(
            name="Comm",
            send_time=0.25,
            debug_logging=True,
        )
        comms.connect(receiver, "incoming")
        comms.run()

        rec_task.run(actor=receiver)
        sen_task.comms = comms
        sen_task.receiver = receiver
        sen_task.run(actor=sender)

        env.run()

        assert env.now == 1.25, "Wrong simulation end time for comms"
        assert receiver.result is not None, "No result for comms"
        assert isinstance(receiver.result, Message), "Wrong result format"
        content = receiver.result.content.data
        assert content["action"] == "move"
        assert content["thought"] == "good"


def test_degraded():
    with EnvironmentContext() as env:
        receiver = ReceiveSend()
        sender = ReceiveSend()

        rec_task = ReceiveTask()
        sen_task = SendTask()

        comms = CommsManager(
            name="Comm",
            send_time=0.25,
            debug_logging=True,
        )
        comms.comms_degraded = True
        comms.connect(receiver, "incoming")
        comms.run()

        rec_task.run(actor=receiver)
        sen_task.comms = comms
        sen_task.receiver = receiver
        sen_task.run(actor=sender)

        env.run(until=4)
        comms.comms_degraded = False

        assert receiver.result is None


def test_blocked():
    with EnvironmentContext() as env:
        receiver = ReceiveSend()
        sender = ReceiveSend()

        rec_task = ReceiveTask()
        sen_task = SendTask()

        comms = CommsManager(
            name="Comm",
            send_time=0.25,
            debug_logging=True,
        )
        comms.connect(receiver, "incoming")
        comms.run()

        comms.blocked_links.append((sender, receiver))

        rec_task.run(actor=receiver)
        sen_task.comms = comms
        sen_task.receiver = receiver
        sen_task.run(actor=sender)

        env.run(until=4)
        comms.comms_degraded = False

        assert receiver.result is None


def test_comms_wait():
    with UP.EnvironmentContext() as env:
        store = Store(env=env)
        data_point = []

        def cback(message):
            data_point.append(message)

        msg = Message(
            sender=UP.Actor(name="me"),
            content=MessageContent(data={"hello": "world"}),
            destination=UP.Actor(name="you"),
        )
        wait_proc = generate_comms_wait(store, cback)
        wait_proc()

        store.put(msg)
        env.run(until=1)
        assert len(data_point) == 1


class Worker(UP.Actor):
    walkie = UP.CommunicationStore(mode="UHF")
    intercom = UP.CommunicationStore(mode="loudspeaker")


def test_worker_talking():
    with EnvironmentContext() as env:
        w1 = Worker(name="worker1")
        w2 = Worker(name="worker2")

        uhf_comms = CommsManager(name="Walkies", mode="UHF")
        loudspeaker_comms = CommsManager(name="Overhead", mode="loudspeaker")

        uhf_comms.run()
        loudspeaker_comms.run()

        evt1 = uhf_comms.make_put("Hello worker", w1, w2)
        evt2 = loudspeaker_comms.make_put("Hello worker", w2, w1)

        def do():
            yield evt1.as_event()
            yield evt2.as_event()

        env.process(do())

        env.run()
        assert len(w2.walkie.items) == 1
        assert len(w1.intercom.items) == 1
