# -*- coding: utf-8 -*-

from ...syntax import macros, nb

def test():
    with nb:
        2 + 3          # top-level expressions autoprint, and auto-assign result to _
        assert _ == 5  # ...and only expressions do that, so...
        _ * 42         # ...here _ stll has the value from the first line.
        assert _ == 210

    try:
        from sympy import symbols
    except ImportError:
        print("*** SymPy not installed, skipping symbolic math test ***")
    else:
        with nb:
            x, y = symbols("x, y")
            x * y
            assert _ == x * y
            3 * _
            assert _ == 3 * x * y

    print("All tests PASSED")