# -*- coding: utf-8 -*-
"""Multi-expression lambdas with implicit do; named lambdas."""

from ...syntax import macros, test, test_raises, warn  # noqa: F401
from ...test.fixtures import session, testset

from ...syntax import (macros, multilambda, namedlambda, quicklambda, f, _,  # noqa: F401, F811
                       envify, local, let, curry, autoreturn)

from functools import wraps

# Not really redefining "curry". The first one went into MacroPy's macro registry,
# and this one is a regular run-time function.
# (Although this does mean the docstring of the macro will not be accessible from here.)
from ...fun import withself, curry  # noqa: F811
from ...tco import trampolined, jump
from ...fploop import looped_over

def runtests():
    with testset("multilambda"):
        with multilambda:
            # use brackets around the body of a lambda to denote a multi-expr body
            echo = lambda x: [print(x), x]
            test[echo("hi there") == "hi there"]

            count = let((x, 0))[  # noqa: F821, the `let` macro defines `x` here.
                      lambda: [x << x + 1,  # noqa: F821
                               x]]  # redundant, but demonstrating multi-expr body.  # noqa: F821
            test[count() == 1]
            test[count() == 2]

            test1 = let((x, 0))[  # noqa: F821
                      lambda: [x << x + 1,      # x belongs to the surrounding let  # noqa: F821
                               local[y << 42],  # y is local to the implicit do  # noqa: F821
                               (x, y)]]  # noqa: F821
            test[test1() == (1, 42)]
            test[test1() == (2, 42)]

            myadd = lambda x, y: [print("myadding", x, y),
                                  local[tmp << x + y],  # noqa: F821, `local[]` defines the name on the LHS of the `<<`.
                                  print("result is", tmp),  # noqa: F821
                                  tmp]  # noqa: F821
            test[myadd(2, 3) == 5]

            # only the outermost set of brackets denote a multi-expr body:
            t = lambda: [[1, 2]]
            test[t() == [1, 2]]

    with testset("namedlambda, basic usage"):
        with namedlambda:
            f1 = lambda x: x**3                      # assignment: name as "f1"
            test[f1.__name__ == "f1"]
            gn, hn = let((x, 42), (g, None), (h, None))[[  # noqa: F821
                           g << (lambda x: x**2),               # env-assignment: name as "g"  # noqa: F821
                           h << f1,                        # still "f1" (RHS is not a literal lambda)  # noqa: F821
                           (g.__name__, h.__name__)]]      # noqa: F821
            test[gn == "g"]
            test[hn == "f1"]

            foo = let[(f7, lambda x: x) in f7]       # let-binding: name as "f7"  # noqa: F821
            test[foo.__name__ == "f7"]

            # function call with named arg
            def foo(func1, func2):
                test[func1.__name__ == "func1"]
                test[func2.__name__ == "func2"]
            foo(func1=lambda x: x**2,  # function call with named arg: name as "func1"
                func2=lambda x: x**2)  # function call with named arg: name as "func2"

            def bar(func1, func2):
                test[func1.__name__ == "<lambda>"]
                test[func2.__name__ == "<lambda>"]
            bar(lambda x: x**2, lambda x: x**2)  # no naming when passed positionally

            def baz(func1, func2):
                test[func1.__name__ == "<lambda>"]
                test[func2.__name__ == "func2"]
            baz(lambda x: x**2, func2=lambda x: x**2)

            # dictionary literal
            d = {"f": lambda x: x**2,  # literal string key in a dictionary literal: name as "f"
                 "g": lambda x: x**2}  # literal string key in a dictionary literal: name as "g"
            test[d["f"].__name__ == "f"]
            test[d["g"].__name__ == "g"]

            # unpacking a dictionary literal into another
            # (makes no sense, but we support it)
            # TODO: Enable once we bump the minimum Python to 3.5+.
            warn["A test that requires Python 3.5 or later is currently disabled for compatibility with 3.4."]
            # d = {"f": lambda x: x**2,
            #      "g": lambda x: x**2,
            #      **{"h": lambda x: x**2,
            #         "k": lambda x: x**2}}
            # test[d["f"].__name__ == "f"]
            # test[d["g"].__name__ == "g"]
            # test[d["h"].__name__ == "h"]
            # test[d["k"].__name__ == "k"]

            # nested dictionary literals
            d = {"func": {"f": lambda x: x**2}}
            test[d["func"]["f"].__name__ == "f"]

            # nested dictionary literals, non-str key
            # TODO: test the case where the outer key contains a literal lambda, too
            d = {42: {"f": lambda x: x**2}}
            test[d[42]["f"].__name__ == "f"]

    with testset("namedlambda, naming a decorated lambda"):
        with namedlambda:
            f2 = trampolined(withself(lambda self, n, acc=1: jump(self, n - 1, acc * n) if n > 1 else acc))
            f2(5000)  # no crash since TCO
            test[f2.__name__ == "f2"]

            # works also with custom decorators
            def mydeco(f):
                @wraps(f)  # important! (without this the name is "decorated", not "f")
                def decorated(*args, **kwargs):
                    return f(*args, **kwargs)
                return decorated
            f3 = mydeco(lambda x: x**2)
            test[f3(10) == 100]
            test[f3.__name__ == "f3"]

            # parametric decorators are defined as usual
            def mypardeco(a, b):
                def mydeco(f):
                    @wraps(f)
                    def decorated(*args, **kwargs):
                        return (a, b, f(*args, **kwargs))
                    return decorated
                return mydeco
            f4 = mypardeco(2, 3)(lambda x: x**2)
            test[f4(10) == (2, 3, 100)]
            test[f4.__name__ == "f4"]

            # to help readability of invocations of parametric decorators on lambdas,
            # we recognize also curry with a lambda as the last argument
            f5 = curry(mypardeco, 2, 3,
                         lambda x: x**2)
            test[f5(10) == (2, 3, 100)]
            test[f5.__name__ == "f5"]

    # also autocurry with a lambda as the last argument is recognized
    # TODO: fix MacroPy #21 properly; https://github.com/azazel75/macropy/issues/21
    with testset("namedlambda, naming an autocurried last arg"):
        with namedlambda:
            with curry:
                f6 = mypardeco(2, 3, lambda x: x**2)
                test[f6(10) == (2, 3, 100)]
                test[f6.__name__ == "f6"]

        # presence of autocurry should not confuse the first-pass output
        with namedlambda:
            with curry:
                foo = let[(f7, None) in f7 << (lambda x: x)]  # noqa: F821
                test[foo.__name__ == "f7"]

                f6 = mypardeco(2, 3, lambda x: x**2)
                test[f6(10) == (2, 3, 100)]
                test[f6.__name__ == "f6"]

    # looped_over overwrites with the result, so nothing to name
    with testset("integration with @looped_over"):
        with namedlambda:
            result = looped_over(range(10), acc=0)(lambda loop, x, acc: loop(acc + x))
            test[result == 45]
            test_raises[AttributeError, result.__name__, "should have returned an int (which has no __name__)"]

            result = curry(looped_over, range(10), 0,
                             lambda loop, x, acc:
                               loop(acc + x))
            test[result == 45]

    with testset("integration: quicklambda, multilambda"):
        # First-pass macros, so in azazel75/macropy/HEAD, approximately the same thing as "with quicklambda, multilambda".
        with quicklambda:
            with multilambda:
                func = f[[local[x << _],  # noqa: F821, F823, `quicklambda` implicitly defines `f[]` to mean `lambda`.
                          local[y << _],  # noqa: F821
                          x + y]]  # noqa: F821
                test[func(1, 2) == 3]

    with testset("envify (formal parameters as an unpythonic env)"):
        with envify:
            def foo(x):
                x = 3  # should become a write into the env
                test[x == 3]
            foo(10)

            def foo(x):
                x = 3
                test[x == 3]
                del x
                # note it's AttributeError since x actually lives in an env
                test_raises[AttributeError, x, "should have deleted x from the implicit env"]  # noqa: F821, the undefined name is the whole point of this test
            foo(10)

        # Star-assignment also works, since Python performs the actual unpacking/packing.
        # We just use a different target for the store.
        with envify:
            def foo(n):
                a, *n, b = (1, 2, 3, 4, 5)  # noqa: F841, `a` and `b` are unused, this is just a silly test.
                test[n == [2, 3, 4]]
            foo(10)

        # The main use case is with lambdas, to do things like this:
        with envify:
            def foo(n):
                return lambda i: n << n + i
            f = foo(10)
            test[f(1) == 11]
            test[f(1) == 12]

        # *starargs and **kwargs are also supported
        with envify:
            def foo(*args):
                test[args == (1, 2, 3)]
                # << assigns in an env, otherwise it's an lshift,
                # so if this mutates, then `args` is in an env.
                args << (4, 5, 6)
                test[args == (4, 5, 6)]
            foo(1, 2, 3)
        with envify:
            def foo(**kwargs):
                test[kwargs == {"a": 1, "b": 2}]
                # likewise here.
                kwargs << {"c": 3, "d": 4}
                test[kwargs == {"c": 3, "d": 4}]
            foo(a=1, b=2)

    with testset("integration: autoreturn, envify"):
        # solution to PG's accumulator puzzle with the fewest elements in the original unexpanded code
        # http://paulgraham.com/icad.html
        with autoreturn, envify:
            def foo(n):
                lambda i: n << n + i
            f = foo(10)
            test[f(1) == 11]
            test[f(1) == 12]

        # or as a one-liner
        with autoreturn, envify:
            foo = lambda n: lambda i: n << n + i
            f = foo(10)
            test[f(1) == 11]
            test[f(1) == 12]

        # pythonic solution with optimal bytecode (doesn't need an extra location to store the accumulator)
        def foo(n):
            def accumulate(i):
                nonlocal n
                n += i
                return n
            return accumulate
        f = foo(10)
        test[f(1) == 11]
        test[f(1) == 12]

if __name__ == '__main__':  # pragma: no cover
    with session(__file__):
        runtests()
