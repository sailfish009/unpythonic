# -*- coding: utf-8 -*-
"""Utilities for writing tests."""

from macropy.core.quotes import macros, q, u, ast_literal
from macropy.core.hquotes import macros, hq  # noqa: F811, F401
from macropy.core import unparse

from ast import Tuple, Str

from ..misc import callsite_filename
from ..conditions import cerror
from ..dynassign import make_dynvar, dyn
from ..collections import box

# Keep a global count (since Python last started) of how many unpythonic_asserts
# have run and how many have failed, so that the client code can easily calculate
# the percentage of tests passed.
#
# We use `box` to keep this simple; its API supports querying and resetting,
# so we don't need to build yet another single-purpose API for these particular
# counters.
tests_run = box(0)
tests_failed = box(0)

make_dynvar(test_signal_errors=False)  # if True, use conditions instead of exceptions to signal failed tests.

# Just a regular function.
def unpythonic_assert(sourcecode, value, filename, lineno, myname=None):
    """Custom assert function, for building test frameworks.

    If the dynvar `test_signal_errors` is truthy, then, upon a failing
    assertion, this will signal the `AssertionError` as a correctable error,
    via unpythonic's condition system (see `unpythonic.conditions.cerror`).

    If that dynvar is falsey (default), the `AssertionError` is raised.

    The idea is that `cerror` allows surrounding code to install a handler that
    invokes the `proceed` restart, so that further tests may continue to run::

        from unpythonic.syntax import macros, test, tests_run, tests_failed

        import sys
        from unpythonic import dyn, handlers, invoke

        def report(err):
            print(err, file=sys.stderr)  # or log or whatever
            invoke("proceed")

        with dyn.let(test_signal_errors=True):  # use conditions instead of exceptions
            with handlers((AssertionError, report)):
                test[2 + 2 == 5]  # fails, but allows further tests to continue
                test[2 + 2 == 4]
                test[17 + 23 == 40, "my named test"]

        assert tests_failed == 1  # we use the type pun that a box is equal to its content.
        assert tests_run == 3

    Parameters:

        `sourcecode` is a string representation of the source code expression
        that is being asserted.

        `value` is the result of running that piece source code, at the call site.
        If `value` is falsey, the assertion fails.

        `filename` is the filename at the call site, if applicable. (If called
        from the REPL, there is no file.)

        `lineno` is the line number at the call site.

        These are best extracted automatically using the `test[]` macro.

        `myname` is an optional string, a name for the assertion being performed.
        It can be used for naming individual tests. The assertion error message
        is either "Named assertion 'foo bar' failed" or "Assertion failed",
        depending on whether `myname` was provided or not.

    No return value.
    """
    tests_run << tests_run.get() + 1

    if value:
        return

    tests_failed << tests_failed.get() + 1

    if myname is not None:
        error_msg = "Named assertion '{}' failed".format(myname)
    else:
        error_msg = "Assertion failed"

    msg = "[{}:{}] {}: {}".format(filename, lineno, error_msg, sourcecode)
    if dyn.test_signal_errors:
        cerror(AssertionError(msg))  # use cerror() so the client code can resume (after logging and such).
    else:
        raise AssertionError(msg)

# The syntax transformer.
def test(tree):
    ln = q[u[tree.lineno]] if hasattr(tree, "lineno") else q[None]
    filename = hq[callsite_filename()]
    asserter = hq[unpythonic_assert]

    # test[expr, "name of this test"]  (like assert expr, name)
    # TODO: Python 3.8+: ast.Constant, no ast.Str
    if type(tree) is Tuple and len(tree.elts) == 2 and type(tree.elts[1]) is Str:
        tree, myname = tree.elts
    # test[expr]  (like assert expr)
    else:
        myname = q[None]

    return q[(ast_literal[asserter])(u[unparse(tree)],
                                     ast_literal[tree],
                                     filename=ast_literal[filename],
                                     lineno=ast_literal[ln],
                                     myname=ast_literal[myname])]
