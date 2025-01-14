# Copyright (C) 2024 by the Georgia Tech Research Institute (GTRI)

# Licensed under the BSD 3-Clause License.
# See the LICENSE file in the project root for complete license terms and disclaimers.

"""This module contains math utility functions to avoid numpy."""

from math import sqrt

VECTOR = list[float] | tuple[float, ...]


def _vector_subtract(A: VECTOR, B: VECTOR) -> list[float]:
    """Subtract equal-sized vectors

    Args:
        A (list[float]): Left vector
        B (list[float]): Right vector

    Returns:
        list[float]: Subtracted vector
    """
    if not (len(A) == len(B)):
        raise ValueError("Vectors are not the same size")

    ret = [a - b for a, b in zip(A, B)]
    return ret


def _vector_add(A: VECTOR, B: VECTOR) -> list[float]:
    """Subtract equal-sized vectors

    Args:
        A (list[float]): Left vector
        B (list[float]): Right vector

    Returns:
        list[float]: Subtracted vector
    """
    if not (len(A) == len(B)):
        raise ValueError("Vectors are not the same size")

    ret = [a + b for a, b in zip(A, B)]
    return ret


def _vector_dot(A: VECTOR, B: VECTOR) -> float:
    """Inner product of two vectors.

    Args:
        A (VECTOR): Left vector
        B (VECTOR): Right vector

    Returns:
        float: inner product
    """
    return sum(a * b for a, b in zip(A, B))


def _vector_norm(arr: VECTOR) -> float:
    """Norm of a vector

    Args:
        arr (VECTOR): vector

    Returns:
        float: norm
    """
    s = sum(a**2 for a in arr)
    return sqrt(s)


def _roots(a: float, b: float, c: float) -> list[float]:
    discriminant = b**2 - 4 * a * c
    if discriminant < 0:
        return []
    root1 = (-b + sqrt(discriminant)) / (2 * a)
    root2 = (-b - sqrt(discriminant)) / (2 * a)
    return [root1, root2]


def _col_mat_mul(col: VECTOR, M: list[list[float]]) -> list[float]:
    """Do a matrix multiplication of a column against a matrix.

    Does col @ M

    Args:
        col (VECTOR): The left vector
        M (list[list[float]]): The matrix

    Returns:
        list[float]: The multiplied result
    """
    if len(col) != len(M):
        raise ValueError("Number of values in col must equal number of rows in M")

    result = [sum(x * y for x, y in zip(col, c)) for c in zip(*M)]

    return result
