# -*- coding: utf-8 -*-
"""Utilities for writing tests.

See also `unpythonic.test.fixtures` for the high-level machinery.
"""

from macropy.core.quotes import macros, q, u, ast_literal, name
from macropy.core.hquotes import macros, hq  # noqa: F811, F401
from macropy.core import unparse

from ast import Tuple, Str, Subscript, Name, Call, copy_location

from ..dynassign import dyn  # for MacroPy's gen_sym
from ..misc import callsite_filename
from ..conditions import cerror, handlers, restarts, invoke
from ..collections import box, unbox
from ..symbol import sym

from .util import isx

from ..test import fixtures

# -----------------------------------------------------------------------------
# Helper for other macros to detect uses of the ones we define here.

# Note the unexpanded `error[]` macro is distinguishable from a call to
# the function `unpythonic.conditions.error`, because a macro invocation
# is an `ast.Subscript`, whereas a function call is an `ast.Call`.
_test_macro_names = ["test", "test_signals", "test_raises", "error", "fail"]
_test_function_names = ["unpythonic_assert",
                        "unpythonic_assert_signals",
                        "unpythonic_assert_raises"]
def istestmacro(tree):
    """Return whether `tree` is an invocation of a testing macro.

    Expanded or unexpanded doesn't matter; this is currently provided
    so that other macros can detect and skip subtrees that invoke a test.
    """
    def isunexpandedtestmacro(tree):
        return (type(tree) is Subscript and
                type(tree.value) is Name and
                tree.value.id in _test_macro_names)
    def isexpandedtestmacro(tree):
        return (type(tree) is Call and
                any(isx(tree.func, fname, accept_attr=False)
                    for fname in _test_function_names))
    return isunexpandedtestmacro(tree) or isexpandedtestmacro(tree)

# -----------------------------------------------------------------------------
# Regular code, no macros yet.

_fail = sym("_fail")  # used by the fail[] macro
_error = sym("_error")  # used by the error[] macro

# Keep a global count (since Python last started) of how many unpythonic_asserts
# have run and how many have failed, so that the client code can easily calculate
# the percentage of tests passed.
#
# We use `box` to keep this simple; its API supports querying and resetting,
# so we don't need to build yet another single-purpose API for these particular
# counters.
tests_run = box(0)
tests_failed = box(0)
tests_errored = box(0)

class TestingException(Exception):
    """Base type for testing-related exceptions."""
class TestFailure(TestingException):
    """Exception type indicating that a test failed."""
class TestError(TestingException):
    """Exception type indicating that a test did not run to completion.

    This can happen due to an unexpected exception, or an unhandled
    `error` (or `cerror`) condition.
    """

_completed = sym("_completed")  # returned normally
_signaled = sym("_signaled")  # via unpythonic.conditions.signal and its sisters
_raised = sym("_raised")  # via raise
def _observe(thunk):
    """Run `thunk` and report how it fared.

    Internal helper for implementing assert functions.

    The return value is:

      - `(_completed, return_value)` if the thunk completed normally
      - `(_signaled, condition_instance)` if a signal from inside
        the dynamic extent of thunk propagated to this level.
      - `(_raised, exception_instance)` if an exception from inside
        the dynamic extent of thunk propagated to this level.
    """
    def intercept(condition):
        if not fixtures._catch_uncaught_signals[0]:
            return  # cancel and delegate to the next outer handler

        def determine_exctype(exc):
            if isinstance(exc, BaseException):  # "signal(SomeError())"
                return type(exc)
            try:
                if issubclass(exc, BaseException):  # "signal(SomeError)"
                    return exc
            except TypeError:  # "issubclass() arg 1 must be a class"
                pass
            assert False  # unpythonic.conditions.signal() does the validation for us

        # If we get an internal signal from this test framework itself, ignore
        # it and let it fall through to the nearest enclosing `testset`, for
        # reporting. This can happen if a `test[]` is nested within a `with
        # test:` block, or if `test[]` expressions are nested.
        exctype = determine_exctype(condition)
        if issubclass(exctype, TestingException):
            return  # cancel and delegate to the next outer handler
        invoke("_got_signal", condition)

    try:
        with restarts(_got_signal=lambda exc: exc) as sig:
            with handlers((Exception, intercept)):
                ret = thunk()
            # We only reach this point if the restart was not invoked,
            # i.e. if thunk() completed normally.
            return _completed, ret
        return _signaled, unbox(sig)
    # This testing framework always signals, never raises, so we don't need any
    # special handling here.
    except Exception as err:  # including ControlError raised by an unhandled `unpythonic.conditions.error`
        return _raised, err

def unpythonic_assert(sourcecode, thunk, *, filename, lineno, message=None):
    """Custom assert function, for building test frameworks.

    Upon a failing assertion, this will *signal* a `TestFailure` as a
    *cerror* (correctable error), via unpythonic's condition system (see
    `unpythonic.conditions.cerror`).

    If a test fails to run to completion due to an unexpected exception or an
    unhandled `error` (or `cerror`) condition, `TestError` is signaled,
    so the caller can easily tell apart which case occurred.

    Using conditions allows the surrounding code to install a handler that
    invokes the `proceed` restart, so upon a test failure, any further tests
    still continue to run::

        from unpythonic.syntax import (macros, test,
                                       tests_run, tests_failed, tests_errored,
                                       TestFailure, TestError)

        import sys
        from unpythonic import invoke, handlers

        def report(err):
            print(err, file=sys.stderr)  # or log or whatever
            invoke("proceed")

        with handlers(((TestFailure, TestError), report)):
            test[2 + 2 == 5]  # fails, but allows further tests to continue
            test[2 + 2 == 4]
            test[17 + 23 == 40, "failure message"]

        # One wouldn't normally use `assert` in a test module that uses `test[]`.
        # This is just to state that in this example, we expect these to hold.
        assert tests_failed == 1  # we use the type pun that a box is equal to its content.
        assert tests_errored == 0
        assert tests_run == 3

    Parameters:

        `sourcecode` is a string representation of the source code expression
        that is being asserted.

        `thunk` is the expression itself, delayed by a lambda, so that this
        function can run the expression at its leisure. If the result of
        running the lambda is falsey, the assertion fails.

        `filename` is the filename at the call site, if applicable. (If called
        from the REPL, there is no file.)

        `lineno` is the line number at the call site.

        These are best extracted automatically using the `test[]` macro.

        `message` is an optional string, included in the generated error message
        if the assertion fails.

    No return value.
    """
    mode, result = _observe(thunk)
    tests_run << unbox(tests_run) + 1

    if message is not None:
        custom_msg = ", with message '{}'".format(message)
    else:
        custom_msg = ""

    # special cases for unconditional failures
    # (e.g. line that should not be reached, optional dependency not installed, ...)
    if mode is _completed and result is _fail:  # fail[...]
        tests_failed << unbox(tests_failed) + 1
        conditiontype = TestFailure
        if message is not None:
            # If a user-given message is specified for `fail[]`, it is all
            # that should be displayed. We don't want confusing noise such as
            # "Test failed"; the intent of signaling an unconditional failure
            # is something different from actually testing the value of an
            # expression.
            error_msg = message
        else:
            error_msg = "Unconditional failure requested, no message."
    elif mode is _completed and result is _error:  # error[...]
        tests_errored << unbox(tests_errored) + 1
        conditiontype = TestError
        if message is not None:
            error_msg = message
        else:
            error_msg = "Unconditional error requested, no message."
    # general cases
    elif mode is _completed:
        if result:
            return
        tests_failed << unbox(tests_failed) + 1
        conditiontype = TestFailure
        error_msg = "Test failed: {}{}".format(sourcecode, custom_msg)
    elif mode is _signaled:
        tests_errored << unbox(tests_errored) + 1
        conditiontype = TestError
        desc = fixtures.describe_exception(result)
        error_msg = "Test errored: {}{}, due to unexpected signal: {}".format(sourcecode, custom_msg, desc)
    else:  # mode is _raised:
        tests_errored << unbox(tests_errored) + 1
        conditiontype = TestError
        desc = fixtures.describe_exception(result)
        error_msg = "Test errored: {}{}, due to unexpected exception: {}".format(sourcecode, custom_msg, desc)

    complete_msg = "[{}:{}] {}".format(filename, lineno, error_msg)

    # We use cerror() to signal a failed/errored test, instead of raising an
    # exception, so the client code can resume (after logging the failure and
    # such).
    #
    # If the client code does not install a handler, then a `ControlError`
    # exception is raised by the condition system; leaving a cerror unhandled
    # is an error.
    cerror(conditiontype(complete_msg))

def unpythonic_assert_signals(exctype, sourcecode, thunk, *, filename, lineno, message=None):
    """Like `unpythonic_assert`, but assert that running `sourcecode` signals `exctype`.

    "Signal" as in `unpythonic.conditions.signal` and its sisters `error`, `cerror`, `warn`.
    """
    def safeissubclass(t, u):
        try:
            return issubclass(t, u)
        except TypeError:  # "issubclass() arg 1 must be a class"
            pass
        return False

    mode, result = _observe(thunk)
    tests_run << unbox(tests_run) + 1

    if message is not None:
        custom_msg = ", with message '{}'".format(message)
    else:
        custom_msg = ""

    if mode is _completed:
        tests_failed << unbox(tests_failed) + 1
        conditiontype = TestFailure
        error_msg = "Test failed: {}{}, expected signal: {}, nothing was signaled.".format(sourcecode, custom_msg, fixtures.describe_exception(exctype))
    elif mode is _signaled:
        # allow both "signal(SomeError())" and "signal(SomeError)"
        if isinstance(result, exctype) or safeissubclass(result, exctype):
            return
        tests_errored << unbox(tests_errored) + 1
        conditiontype = TestError
        desc = fixtures.describe_exception(result)
        error_msg = "Test errored: {}{}, expected signal: {}, got unexpected signal: {}".format(sourcecode, custom_msg, fixtures.describe_exception(exctype), desc)
    else:  # mode is _raised:
        tests_errored << unbox(tests_errored) + 1
        conditiontype = TestError
        desc = fixtures.describe_exception(result)
        error_msg = "Test errored: {}{}, expected signal: {}, got unexpected exception: {}".format(sourcecode, custom_msg, fixtures.describe_exception(exctype), desc)

    complete_msg = "[{}:{}] {}".format(filename, lineno, error_msg)
    cerror(conditiontype(complete_msg))

def unpythonic_assert_raises(exctype, sourcecode, thunk, *, filename, lineno, message=None):
    """Like `unpythonic_assert`, but assert that running `sourcecode` raises `exctype`."""
    def safeissubclass(t, u):
        try:
            return issubclass(t, u)
        except TypeError:  # "issubclass() arg 1 must be a class"
            pass
        return False

    mode, result = _observe(thunk)
    tests_run << unbox(tests_run) + 1

    if message is not None:
        custom_msg = ", with message '{}'".format(message)
    else:
        custom_msg = ""

    if mode is _completed:
        tests_failed << unbox(tests_failed) + 1
        conditiontype = TestFailure
        error_msg = "Test failed: {}{}, expected exception: {}, nothing was raised.".format(sourcecode, custom_msg, fixtures.describe_exception(exctype))
    elif mode is _signaled:
        tests_errored << unbox(tests_errored) + 1
        conditiontype = TestError
        desc = fixtures.describe_exception(result)
        error_msg = "Test errored: {}{}, expected exception: {}, got unexpected signal: {}".format(sourcecode, custom_msg, fixtures.describe_exception(exctype), desc)
    else:  # mode is _raised:
        # allow both "raise SomeError()" and "raise SomeError"
        if isinstance(result, exctype) or safeissubclass(result, exctype):
            return
        tests_errored << unbox(tests_errored) + 1
        conditiontype = TestError
        desc = fixtures.describe_exception(result)
        error_msg = "Test errored: {}{}, expected exception: {}, got unexpected exception: {}".format(sourcecode, custom_msg, fixtures.describe_exception(exctype), desc)

    complete_msg = "[{}:{}] {}".format(filename, lineno, error_msg)
    cerror(conditiontype(complete_msg))


# -----------------------------------------------------------------------------
# Syntax transformers for the macros.

def _fail_or_error_expr(tree, syntaxname, marker):
    # TODO: Python 3.8+: ast.Constant, no ast.Str
    if type(tree) is not Str:
        assert False, "expected {stx}[message]".format(stx=syntaxname)
    thetuple = q[(ast_literal[marker], ast_literal[tree])]
    thetuple = copy_location(thetuple, tree)
    return test_expr(thetuple)

def fail_expr(tree):
    return _fail_or_error_expr(tree, "fail", hq[_fail])
def error_expr(tree):
    return _fail_or_error_expr(tree, "error", hq[_error])

# -----------------------------------------------------------------------------
# Expr variants.

def test_expr(tree):
    ln = q[u[tree.lineno]] if hasattr(tree, "lineno") else q[None]
    filename = hq[callsite_filename()]
    asserter = hq[unpythonic_assert]

    # test[expr, name]  (like assert expr, name)
    # TODO: Python 3.8+: ast.Constant, no ast.Str
    if type(tree) is Tuple and len(tree.elts) == 2 and type(tree.elts[1]) is Str:
        tree, message = tree.elts
    # test[expr]  (like assert expr)
    else:
        message = q[None]

    # The lambda delays the execution of the test expr until `unpythonic_assert` gets control.
    return q[(ast_literal[asserter])(u[unparse(tree)],
                                     lambda: ast_literal[tree],
                                     filename=ast_literal[filename],
                                     lineno=ast_literal[ln],
                                     message=ast_literal[message])]

def _test_expr_signals_or_raises(tree, syntaxname, asserter):
    ln = q[u[tree.lineno]] if hasattr(tree, "lineno") else q[None]
    filename = hq[callsite_filename()]

    # test_signals[exctype, expr, name]
    # TODO: Python 3.8+: ast.Constant, no ast.Str
    if type(tree) is Tuple and len(tree.elts) == 3 and type(tree.elts[2]) is Str:
        exctype, tree, message = tree.elts
    # test_signals[exctype, expr]
    elif type(tree) is Tuple and len(tree.elts) == 2:
        exctype, tree = tree.elts
        message = q[None]
    else:
        assert False, "Expected one of {stx}[exctype, expr], {stx}[exctype, expr, message]".format(stx=syntaxname)

    return q[(ast_literal[asserter])(ast_literal[exctype],
                                     u[unparse(tree)],
                                     lambda: ast_literal[tree],
                                     filename=ast_literal[filename],
                                     lineno=ast_literal[ln],
                                     message=ast_literal[message])]

def test_expr_signals(tree):
    return _test_expr_signals_or_raises(tree, "test_signals", hq[unpythonic_assert_signals])
def test_expr_raises(tree):
    return _test_expr_signals_or_raises(tree, "test_raises", hq[unpythonic_assert_raises])

# -----------------------------------------------------------------------------
# Block variants.

def _make_identifier(s):
    """Given a human-readable label, attempt to convert it into an identifier."""
    maybe_identifier = s.replace(" ", "_")
    # Lowercase just the first letter to follow Python function naming conventions.
    maybe_identifier = maybe_identifier[0].lower() + maybe_identifier[1:]
    if maybe_identifier.isidentifier():
        return maybe_identifier
    return None

# The strategy is we capture the block body into a new function definition,
# and then apply `test_expr` to a call to that function.
#
# The function is named with a MacroPy gen_sym; if the test has a failure
# message, that message is mangled into a function name if reasonably possible.
# When no message is given or mangling would be nontrivial, we treat the test as
# an anonymous test block.
#
def test_block(block_body, args):
    # with test(message):
    # TODO: Python 3.8+: ast.Constant, no ast.Str
    function_name = "anonymous_test_block"
    if len(args) == 1 and type(args[0]) is Str:
        message = args[0]
        # Name the generated function using the failure message when possible.
        maybe_function_name = _make_identifier(message.s)
        if maybe_function_name is not None:
            function_name = maybe_function_name
    # with test:
    elif len(args) == 0:
        message = None
    else:
        assert False, 'Expected `with test:` or `with test(message):`'

    gen_sym = dyn.gen_sym
    final_function_name = gen_sym(function_name)

    thecall = q[name[final_function_name]()]
    if message is not None:
        # Fill in the source line number; the `test_expr_raises` syntax transformer needs
        # to have it in the top-level node of the `tree` we hand to it.
        thetuple = q[(ast_literal[thecall], ast_literal[message])]
        thetuple = copy_location(thetuple, block_body[0])
        thetest = test_expr(thetuple)
    else:
        thecall = copy_location(thecall, block_body[0])
        thetest = test_expr(thecall)

    with q as newbody:
        def _():
            ...
        ast_literal[thetest]
    thefunc = newbody[0]
    thefunc.name = final_function_name
    thefunc.body = block_body
    # Add a `return True` to satisfy the test when the function returns normally.
    with q as thereturn:
        return True
    thefunc.body.append(thereturn)
    return newbody

def _test_block_signals_or_raises(block_body, args, syntaxname, transformer):
    # with test_raises(exctype, message):
    # TODO: Python 3.8+: ast.Constant, no ast.Str
    function_name = "anonymous_test_block"
    if len(args) == 2 and type(args[1]) is Str:
        exctype, message = args
        # Name the generated function using the failure message when possible.
        maybe_function_name = _make_identifier(message.s)
        if maybe_function_name is not None:
            function_name = maybe_function_name
    # with test_raises(exctype):
    elif len(args) == 1:
        exctype = args[0]
        message = None
    else:
        assert False, 'Expected `with {stx}(exctype):` or `with {stx}(exctype, message):`'.format(stx=syntaxname)

    gen_sym = dyn.gen_sym
    final_function_name = gen_sym(function_name)

    thecall = q[name[final_function_name]()]
    if message is not None:
        # Fill in the source line number; the `test_expr_raises` and
        # `test_expr_signals` syntax transformers need to have it in
        # the top-level node of the `tree` we hand to it.
        thetuple = q[(ast_literal[exctype], ast_literal[thecall], ast_literal[message])]
        thetuple = copy_location(thetuple, block_body[0])
        thetest = transformer(thetuple)
    else:
        thetuple = q[(ast_literal[exctype], ast_literal[thecall])]
        thetuple = copy_location(thetuple, block_body[0])
        thetest = transformer(thetuple)

    with q as newbody:
        def _():
            ...
        ast_literal[thetest]
    thefunc = newbody[0]
    thefunc.name = final_function_name
    thefunc.body = block_body
    return newbody

def test_block_signals(block_body, args):
    return _test_block_signals_or_raises(block_body, args, "test_signals", test_expr_signals)
def test_block_raises(block_body, args):
    return _test_block_signals_or_raises(block_body, args, "test_raises", test_expr_raises)
