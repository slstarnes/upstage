# Copyright (C) 2024 by the Georgia Tech Research Institute (GTRI)

# Licensed under the BSD 3-Clause License.
# See the LICENSE file in the project root for complete license terms and disclaimers.

import random

import pytest


@pytest.fixture()
def atl():
    return (33.7490, -84.3880)


@pytest.fixture()
def atl_north():
    return (33.9, -84.3880)


@pytest.fixture()
def atl_south():
    return (33.7489, -84.3880)


@pytest.fixture()
def nas():
    return (36.1627, -86.7816)


@pytest.fixture()
def nyc():
    return (40.7128, -74.0060)


@pytest.fixture()
def lax():
    return (34.0522, -118.2437)


@pytest.fixture()
def tall():
    return (30.4383, -84.2807)


def randvals(rows, cols):
    ans = []
    for _ in range(rows):
        v = [random.random() for _ in range(cols)]
        ans.append(v)
    return ans


@pytest.fixture()
def random_lla():
    lla = randvals(10, 3)
    lat, lon, alt = zip(*lla)
    lat = [-90 + 180 * la for la in lat]
    lon = [-180 + 360 * lo for lo in lon]
    alt = [a * 10_000 for a in alt]
    return [(a, b, c) for a, b, c in zip(lat, lon, alt)]


@pytest.fixture()
def local_lla():
    lla_base = [33.7490, -84.3880, 320]
    lla = randvals(10, 3)
    lat, lon, alt = zip(*lla)
    lat = [lla_base[0] + 5 * (-1 + 2 * la) for la in lat]
    lon = [lla_base[1] + 5 * (-1 + 2 * lo) for lo in lon]
    alt = [lla_base[2] + 1000 * (-1 + 2 * a) for a in alt]
    ans = [tuple(lla_base)] + [(a, b, c) for a, b, c in zip(lat, lon, alt)]
    return ans


@pytest.fixture(
    params=[
        (0, 0, 0, 100, "nmi", ["ENTER", "EXIT"]),
        (5000, 5000, 0, 100, "nmi", ["ENTER", "EXIT"]),
        (0, 0, 0, 190, "nmi", ["START_INSIDE", "EXIT"]),
        (5000, 5000, 0, 190, "nmi", ["START_INSIDE", "EXIT"]),
        (0, 0, 0, 220, "nmi", ["START_INSIDE", "END_INSIDE"]),
        (5000, 5000, 0, 220, "nmi", ["START_INSIDE", "END_INSIDE"]),
    ],
)
def intersect_positions(nas, tall, atl, request):
    # degrees and meters
    start_alt, finish_alt, sensor_alt, sensor_range, range_units, answer = request.param

    start_lla = [nas[0], nas[1], start_alt]
    finish_lla = [tall[0], tall[1], finish_alt]
    sensor_lla = [atl[0], atl[1], sensor_alt]
    return [start_lla, finish_lla, sensor_lla], sensor_range, range_units, answer


@pytest.fixture
def short_intersections():
    start_lla = (61.10051577739581, -154.64858364056806, 100.0)
    finish_lla = (61.15466234550906, -154.77763243723408, 100.0)
    sensor_lla = (58.67779481, -154.11651336, 0.0)
    sensor_radius = 277799.8988808368
    return [start_lla, finish_lla, sensor_lla], sensor_radius, "m"
