# -*- coding: utf-8 -*-
"""Automatic lazy evaluation of function arguments."""

from ...misc import raisef

from ...syntax import macros, lazify

from macropy.tracing import macros, show_expanded

def test():
    with show_expanded:
      # in a "with lazify" block, function arguments are evaluated only when actually used.
      with lazify:
        def my_if(p, a, b):
            if p:
                return a  # b never evaluated in this code path
            else:
                return b  # a never evaluated in this code path

        assert my_if(True, 23, 0) == 23
        assert my_if(False, 0, 42) == 42

        # note the raisef() calls; in regular Python, they'd run anyway before my_if() gets control.
        assert my_if(True, 23, raisef(RuntimeError, "I was evaluated!")) == 23
        assert my_if(False, raisef(RuntimeError, "I was evaluated!"), 42) == 42

        # In this example, the divisions by zero are never performed.
        assert my_if(True, 23, 1/0) == 23
        assert my_if(False, 1/0, 42) == 42

    print("All tests PASSED")