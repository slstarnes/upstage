# Copyright (C) 2024 by the Georgia Tech Research Institute (GTRI)

# Licensed under the BSD 3-Clause License.
# See the LICENSE file in the project root for complete license terms and disclaimers.

import upstage.api as UP


class Dummy(UP.Actor):
    number = UP.State()
    results = UP.State(default=0)


class Example(UP.Task):
    def task(self, *, actor):
        yield UP.Wait(actor.number)
        actor.number /= 2


class OtherExample(UP.Task):
    def task(self, *, actor):
        actor.results += 1
        yield UP.Wait(100)

    def on_interrupt(self, *, actor, cause):
        super().on_interrupt(actor=actor, cause=cause)
        return self.INTERRUPT.RESTART


fact = UP.TaskNetworkFactory(
    "example",
    {"Runner": Example},
    {"Runner": {"default": "Runner", "allowed": ["Runner"]}},
)

fact2 = UP.TaskNetworkFactory(
    "side",
    {"Side": OtherExample},
    {"Side": {"default": "Side", "allowed": ["Side"]}},
)


def test_creation():
    with UP.EnvironmentContext() as env:
        actor = Dummy(name="example", number=10)
        nuc = UP.TaskNetworkNucleus(actor=actor)
        task_net = fact.make_network()
        actor.add_task_network(task_net)
        nuc.add_network(task_net, [])
        # start the task network
        actor.start_network_loop("example", init_task_name="Runner")
        env.run(until=18)
        assert actor.number == 1.25


def test_with_interrupt():
    with UP.EnvironmentContext() as env:
        actor = Dummy(name="example", number=10, results=0)
        nuc = UP.TaskNetworkNucleus(actor=actor)

        task_net = fact.make_network()
        actor.add_task_network(task_net)
        nuc.add_network(task_net, [])

        task_net_2 = fact2.make_network()
        actor.add_task_network(task_net_2)
        nuc.add_network(task_net_2, ["number"])

        actor.start_network_loop("example", init_task_name="Runner")
        actor.start_network_loop("side", init_task_name="Side")

        env.run(until=15)
        assert actor.results == 2
