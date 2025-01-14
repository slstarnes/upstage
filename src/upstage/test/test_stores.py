# Copyright (C) 2024 by the Georgia Tech Research Institute (GTRI)

# Licensed under the BSD 3-Clause License.
# See the LICENSE file in the project root for complete license terms and disclaimers.

import pytest

from upstage.actor import Actor
from upstage.base import EnvironmentContext
from upstage.events import FilterGet
from upstage.resources.monitoring import (
    SelfMonitoringContainer,
    SelfMonitoringFilterStore,
    SelfMonitoringReserveStore,
    SelfMonitoringSortedFilterStore,
    SelfMonitoringStore,
)
from simpy import Store
from upstage.resources.reserve import ReserveStore
from upstage.resources.sorted import SortedFilterGet, SortedFilterStore

MAX_RUN_TIME = 10.0


def getter(env, store, wait=1.0, cback=None, **kwargs):
    yield env.timeout(wait)
    get = store.get(**kwargs)
    if cback is not None:
        get.callbacks.append(cback)
    item = yield get
    return item


def sorted_filter_getter(env, store, wait, filter, sorter):
    yield env.timeout(wait)
    evt = SortedFilterGet(
        store,
        filter,
        sorter,
    )
    item = yield evt.as_event()
    return item


def putter(env, store, item, wait=0.0, cback=None, **kwargs):
    yield env.timeout(wait)
    put = store.put(item, **kwargs)
    if cback is not None:
        put.callbacks.append(cback)
    yield put


def test_notifying_store():
    notifications = []

    def callback(*args, **kwargs):
        assert len(kwargs) == 0
        notifications.append(args)

    with EnvironmentContext() as env:
        store = Store(env=env)

        def sim():
            item = "an item"
            yield env.process(putter(env, store, item, cback=callback))
            retrieved_item = yield env.process(getter(env, store, cback=callback))
            assert item == retrieved_item

        env.process(sim())

        env.run(until=MAX_RUN_TIME)

        assert len(notifications) == 2


def test_sorted_filter_store():
    with EnvironmentContext() as env:
        store = SortedFilterStore(env=env)

        def get_proc():
            item = yield env.process(
                getter(
                    env,
                    store=store,
                    filter=lambda x: isinstance(x, int | float),
                    sorter=lambda x: (-x,),
                    wait=0.0,
                )
            )
            return item

        def sim():
            env.process(putter(env, store, 10, wait=0.0))
            env.process(putter(env, store, 1, wait=0.0))

            item = yield env.process(get_proc())

            assert item == 10

        env.process(sim())

        env.run(until=MAX_RUN_TIME)


def test_sorted_filter_store_upstage_get():
    with EnvironmentContext() as env:
        store = SortedFilterStore(env=env)

        def get_proc():
            item = yield env.process(
                sorted_filter_getter(
                    env,
                    store=store,
                    filter=lambda x: isinstance(x, int | float),
                    sorter=lambda x: (-x,),
                    wait=0.0,
                )
            )
            return item

        def sim():
            env.process(putter(env, store, 10, wait=0.0))
            env.process(putter(env, store, 1, wait=0.0))

            item = yield env.process(get_proc())

            assert item == 10

        env.process(sim())

        env.run(until=MAX_RUN_TIME)


def test_reserve_store():
    with EnvironmentContext() as env:
        store = ReserveStore(
            env=env,
            capacity=10,
            init=10,
        )
        assert store.available == 10

        class R(Actor): ...

        requestor = R(name="wanter")

        req = store.reserve(requestor, 8, expiration=12)
        assert req is not False
        req1 = store.reserve(R(name="other"), 8)
        assert not req1

        assert store.available == 2
        assert len(store._queued) == 1
        env.run(until=1)
        store.cancel_request(requestor)
        assert len(store._queued) == 0
        assert store.available == 10

        req = store.reserve(requestor, 8, expiration=8)
        assert req is not False
        env.run(until=13)
        assert len(store.queued) == 0
        assert store.available == 10
        with pytest.raises(ValueError):
            store.take(requestor)

        req = store.reserve(requestor, 8, expiration=8)
        env.run(until=14)
        assert store.take(requestor) == 8
        env.run(until=30)
        assert store.available == 2

        with pytest.raises(ValueError):
            store.put(100, capacity_increase=False)

        store.put(3)
        assert store.available == 5


def test_self_monitoring_filter_store():
    with EnvironmentContext() as env:
        store = SelfMonitoringFilterStore(env=env)

        def filter(item: str) -> bool:
            return "Another" in item

        def proc():
            yield store.put("The Item")
            yield store.put("Another Item")
            evt = FilterGet(
                store,
                filter,
            )
            item = yield evt.as_event()
            return item

        def sim():
            item = yield env.process(proc())
            assert item == "Another Item"

        env.process(sim())

        env.run(until=MAX_RUN_TIME)


def test_self_monitoring_sorted_filter_store():
    with EnvironmentContext() as env:
        store = SelfMonitoringSortedFilterStore(env=env)

        def get_proc():
            item = yield env.process(
                getter(
                    env,
                    store=store,
                    filter=lambda x: isinstance(x, int | float),
                    sorter=lambda x: (-x,),
                    wait=0.0,
                ),
            )
            return item

        def sim():
            env.process(putter(env, store, 10, wait=0.0))
            env.process(putter(env, store, 1, wait=0.0))

            item = yield env.process(get_proc())

            assert item == 10

        env.process(sim())

        env.run(until=MAX_RUN_TIME)


def test_self_monitoring_store():
    with EnvironmentContext() as env:
        SelfMonitoringStore(env)
        env.run(until=MAX_RUN_TIME)


def test_self_monitoring_reserve_store():
    with EnvironmentContext() as env:
        SelfMonitoringReserveStore(env)
        env.run(until=MAX_RUN_TIME)


def test_self_monitoring_container():
    with EnvironmentContext() as env:
        con = SelfMonitoringContainer(env, capacity=10)

        def sim():
            evt = con.put(5)
            yield evt
            evt = con.get(3)
            yield evt

        env.process(sim())
        env.run()
        assert len(con._quantities) == 3
        assert [0, 5, 2] == [x[1] for x in con._quantities]
