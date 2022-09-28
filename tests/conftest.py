import itertools
import random

import pytest

from dndice.lib.evaltree import EvalTree, EvalTreeNode


def trees_equal(a: EvalTree, b: EvalTree) -> bool:
    for nodeA, nodeB in itertools.zip_longest(a.pre_order(), b.pre_order(),
                                              fillvalue=EvalTreeNode(None)):
        if nodeA.payload != nodeB.payload:
            return False
    return True


@pytest.fixture
def mock_randint(monkeypatch):
    rands = itertools.chain([1, 20, 1, 20, 1, 20], itertools.repeat(4))

    def randint(start, end):
        return next(rands)

    monkeypatch.setattr(random, "randint", randint)


@pytest.fixture
def tree_eq(monkeypatch):
    monkeypatch.setattr(EvalTree, "__eq__", trees_equal)
