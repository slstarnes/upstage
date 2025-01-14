# Copyright (C) 2024 by the Georgia Tech Research Institute (GTRI)

# Licensed under the BSD 3-Clause License.
# See the LICENSE file in the project root for complete license terms and disclaimers.

import simpy as SIM

import upstage.api as UP

from .mover import Mover


class Flyer(Mover):
    fuel_capacity = UP.State(valid_types=(float,), frozen=True)
    fuel_draw = UP.State(valid_types=(int, float), frozen=True)
    messages = UP.ResourceState(default=SIM.Store, valid_types=(SIM.Store,))
    approach = UP.State(default=False, valid_types=(bool,), recording=True)


class MissionPlanning(UP.Task):
    def task(self, *, actor):
        # Figure out the time to reach the right waypoint
        # Schedule the approach network
        # and a speed change for that time.
        # Also, kick off the flying.
        refuel_point = self.get_actor_knowledge(actor, "meetup", must_exist=True)
        time_to_point = (actor.location - refuel_point) / actor.speed
        yield UP.Wait(time_to_point)
        actor.approach = True


mission_plan_net = UP.TaskNetworkFactory.from_single_terminating(
    "plan", MissionPlanning
)


class ApproachWait(UP.Task):
    def task(self, *, actor):
        yield UP.Event()

    def on_interrupt(self, *, actor, cause):
        assert cause.state_name == "approach"
        return self.INTERRUPT.END


class ApproachMothership(UP.Task):
    def task(self, *, actor):
        the_mothership = self.get_actor_knowledge(actor, "mothership", must_exist=True)
        refuel_speed = self.get_actor_knowledge(actor, "refuel_speed", must_exist=True)
        actor.speed = refuel_speed  # NUCLEUS INTERACTION
        yield UP.Put(the_mothership.messages, (actor, -actor.fuel_draw))
        proceed = yield UP.Get(actor.messages)
        assert proceed == "GO"


class Refuel(UP.Task):
    def task(self, *, actor: UP.Actor):
        # ignore any particular timing to "full fuel"
        needed = actor.fuel_capacity - actor.fuel
        # we're here if we got the message to go
        actor.activate_state(
            state="fuel",
            task=self,
            rate=actor.fuel_draw,
        )
        time = needed / actor.fuel_draw
        yield UP.Wait(time)
        actor.deactivate_state(state="fuel", task=self)
        the_mothership = self.get_actor_knowledge(actor, "mothership", must_exist=True)
        yield UP.Put(the_mothership.messages, (actor, 0))
        self.set_actor_knowledge(actor, "done_refueling", True, overwrite=True)


flyer_refuel_factory = UP.TaskNetworkFactory.from_ordered_loop(
    "flyer_refuel",
    [ApproachWait, ApproachMothership, Refuel],
)
