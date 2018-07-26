# Unpythonic: `let`, assign-once, dynamic scoping

Simple constructs that change the rules.

```python
from unpythonic import *
```

### Assign-once environment

```python
with assignonce() as e:
    e.foo = "bar"           # new definition, ok
    e.set("foo", "tavern")  # explicitly rebind e.foo, ok
    e << ("foo", "tavern")  # same thing (but return e instead of new value, suitable for chaining)
    e.foo = "quux"          # AttributeError, e.foo already defined.
```

### Multiple expressions in a lambda

```python
f1 = lambda x: begin(print("cheeky side effect"),
                     42*x)
f1(2)  # --> 84

f2 = lambda x: begin0(42*x,
                      print("cheeky side effect"))
f2(2)  # --> 84
```

Actually a tuple in disguise. If worried about memory consumption, use `lazy_begin` and `lazy_begin0` instead, which indeed use loops. The price is the need for a lambda wrapper for each expression to delay evaluation, see [`tour.py`](tour.py) for details.

Note also it's only for side effects, since there's no way to define new names, except...

### ``let``, ``letrec``

Use a `lambda e: ...` to supply the environment to the body:

```python
u = lambda lst: let(seen=set(),
                    body=lambda e:
                           [e.seen.add(x) or x for x in lst if x not in e.seen])
L = [1, 1, 3, 1, 3, 2, 3, 2, 2, 2, 4, 4, 1, 2, 3]
u(L)  # --> [1, 3, 2, 4]
```

In case of `letrec`, each binding takes a `lambda e: ...`, too:

```python
u = lambda lst: letrec(seen=lambda e:
                              set(),
                       see=lambda e:
                              lambda x:
                                begin(e.seen.add(x),
                                      x),
                       body=lambda e:
                              [e.see(x) for x in lst if x not in e.seen])

letrec(evenp=lambda e:
               lambda x:
                 (x == 0) or e.oddp(x - 1),
       oddp=lambda e:
               lambda x:
                 (x != 0) and e.evenp(x - 1),
       body=lambda e:
               e.evenp(42))  # --> True
```

**CAUTION**: bindings are initialized in an arbitrary order, also in ``letrec``. This is a limitation of the kwargs abuse. If you need left-to-right initialization, ``unpythonic.lispylet`` provides an alternative implementation with positional syntax and more parentheses:

```python
from unpythonic.lispylet import *  # override the default "let" implementation

letrec((('a', 1),
        ('b', lambda e:
                e.a + 1)),
       lambda e:
         e.b)  # --> 2

letrec((("evenp", lambda e:
                    lambda x:
                      (x == 0) or e.oddp(x - 1)),
        ("oddp",  lambda e:
                    lambda x:
                      (x != 0) and e.evenp(x - 1))),
       lambda e:
         e.evenp(42))  # --> True
```

In ``lispylet``, the syntax is `let(bindings, body)`, where bindings is a list of `(name, value)` pairs.

In ``lispylet.letrec``, if `value` is callable, it will be called with the environment as its only argument when the environment is being set up, and the result of the call is bound to `name`. The expression may refer to bindings above it in the same ``letrec`` (this behaves like [Racket](http://racket-lang.org/)'s `let*`). Function definitions may be mutually recursive.

To store a callable `f` into a ``lispylet.letrec`` binding, `value` must be ``lambda e: f``, whether or not `f` actually uses the environment. Otherwise `f` itself will be called with the environment as its argument (likely not what was intended). Here `f` itself may be any callable. Examples of correct usage:

```python
u = lambda lst: letrec((("seen", set()),
                        ("see",  lambda e:
                                   lambda x:  # a function, needs "lambda e: ..."
                                     begin(e.seen.add(x),
                                           x))),
                       lambda e:
                         [e.see(x) for x in lst if x not in e.seen])

letrec((('a', 2),
        ('f', lambda e:
                lambda x:  # a function, needs "lambda e: ..." even though it doesn't use e
                  42*x)),
       lambda e:
         e.a * e.f(1))  # --> 84

square = lambda x: x**2
letrec((('a', 2),
        ('f', lambda e: square)),  # callable, needs "lambda e: ..."
       lambda e: e.a * e.f(10))  # --> 200

def mul(x, y):
    return x * y
letrec((('a', 2),
        ('f', lambda e: mul)),  # same here, "mul" is a callable
       lambda e: e.a * e.f(3, 4))  # --> 24

from functools import partial
double = partial(mul, 2)
letrec((('a', 2),
        ('f', lambda e: double)),  # "double" is a callable
       lambda e: e.a * e.f(3))  # --> 12

class TimesA:
    def __init__(self, a):
        self.a = a
    def __call__(self, x):
        return self.a * x
times5 = TimesA(5)
letrec((('a', 2),
        ('f', lambda e: times5)),  # "times5" is a callable
       lambda e: e.a * e.f(3))  # --> 30
```

The ``lambda e: ...`` receives the environment. The result of the call (where `e` is now bound by closure) is bound to ``name``.

**Back to the default implementation**. Traditional *let over lambda*. The inner ``lambda`` is the definition of the function ``counter``:

```python
counter = let(x=0,
              body=lambda e:
                     lambda:
                       begin(e.set("x", e.x + 1),  # can also use e << ("x", e.x + 1)
                             e.x))
counter()  # --> 1
counter()  # --> 2
```

Compare this [Racket](http://racket-lang.org/) equivalent (here using `sweet-exp` [[1]](https://srfi.schemers.org/srfi-110/srfi-110.html) [[2]](https://docs.racket-lang.org/sweet/) for pythonic layout):

```racket
define counter
  let ([x 0])
    λ ()  ; <-- λ has an implicit begin(), so we don't need to explicitly have one
      set! x {x + 1}
      x
counter()  ; --> 1
counter()  ; --> 2
```

*Let over def* decorator ``@dlet``:

```python
@dlet(x=0)
def counter(*, env=None):  # named argument "env" filled in by decorator
    env.x += 1
    return env.x
counter()  # --> 1
counter()  # --> 2
```

The **environment** implementation used by all the ``let`` constructs and ``assignonce`` (but **not** by `dyn`) is essentially a bunch with iteration and subscripting support. For details, see `unpythonic.env` (not imported by default). This allows things like:

```python
let(x=1, y=2, z=3,
    body=lambda e:
           [(name, 2*e[name]) for name in e])  # --> [('y', 4), ('z', 6), ('x', 2)]
```

It also works as a bare bunch, and supports printing for debugging:

```python
from unpythonic.env import env

e = env(s="hello", orange="fruit", answer=42)
print(e)  # --> <env object at 0x7ff784bb4c88: {orange='fruit', s='hello', answer=42}>
print(e.s)  # --> hello

d = {'monty': 'python', 'pi': 3.14159}
e = env(**d)
print(e)  # --> <env object at 0x7ff784bb4c18: {pi=3.14159, monty='python'}>
print(e.monty)  # --> python
```

Finally, it supports the context manager:

```python
with env(x=1, y=2, z=3) as e2:
    ...  # ...code that uses e2...
print(e2)  # empty!
```

When the `with` block exits, the environment forgets all its bindings. The environment instance itself remains alive due to Python's scoping rules.

### Dynamic scoping

Via lexical scoping in disguise. There's a singleton, `dyn`, which emulates dynamic scoping (like [Racket](http://racket-lang.org/)'s [`parameterize`](https://docs.racket-lang.org/guide/parameterize.html)):

```python
def f():  # no "a" in lexical scope here
    assert dyn.a == 2

def g():
    with dyn.let(a=2, b="foo"):
        assert dyn.a == 2

        f()

        with dyn.let(a=3):  # dynamic scopes can be nested
            assert dyn.a == 3

        # now "a" has reverted to its previous value
        assert dyn.a == 2

    print(dyn.b)  # AttributeError, dyn.b no longer exists
g()
```

Dynamic variables can only be set using `with dyn.let(...)`. No `set`, `<<`, unlike in the other `unpythonic` environments.

Once set, a dynamic variable exists for the dynamic extent of the `with` block (i.e. until the block exits). Inner dynamic scopes shadow outer ones. Dynamic variables are seen also by code that is outside the lexical scope where the `with dyn.let` resides.

The dynamic scope stack is thread-local. Any newly spawned threads inherit the then-current state of the dynamic scope stack **from the main thread** (not the parent thread). This is mainly because Python's `threading` module gives no tools to detect which thread spawned the current one. (If someone knows a simple solution, PRs welcome!)

### ``def`` as a code block

A convenience feature for fueling different thinking, compare the `something` in `call-with-something` in Lisps. A `def` is really just a new lexical scope to hold code to run later... or right now!

*Make temporaries fall out of scope as soon as no longer needed*:

```python
@immediate
def x():
    a = 2  #    many temporaries that help readability...
    b = 3  # ...of this calculation, but would just pollute locals...
    c = 5  # ...after the block exits
    return a * b * c
print(x)  # 30
```

*Multi-break out of nested loops* - `continue`, `break` and `return` are really just second-class [ec](https://docs.racket-lang.org/reference/cont.html#%28def._%28%28lib._racket%2Fprivate%2Fletstx-scheme..rkt%29._call%2Fec%29%29)s:

```python
@immediate
def result():
    for x in range(10):
        for y in range(10):
            if x * y == 42:
                return (x, y)
            ... # more code here
print(result)  # (6, 7)
```

*Twist the meaning of `def` into a "let statement"* (but see `blet`, `bletrec`):

```python
@immediate
def result(x=1, y=2, z=3):
    return x * y * z
print(result)  # 6
```

*Letrec without `letrec`*, when it doesn't have to be an expression:

```python
@immediate
def t():
    def evenp(x): return x == 0 or oddp(x - 1)
    def oddp(x): return x != 0 and evenp(x - 1)
    return evenp(42)
print(t)  # True
```

Essentially the implementation is just `def immediate(thunk): return thunk()`. The point is to:

 - Make it explicit right at the definition site that this block is going to be run ``@immediate``ly (in contrast to an explicit call and assignment *after* the definition). Collect related information into one place. Align the ordering of the presentation with the ordering of the thought process, reducing the need to skip back and forth when reading and writing code.

 - Help eliminate errors, in the same way as the habit of typing parentheses only in pairs. There's no risk of forgetting to call the block after the possibly lengthy process of thinking through and writing the definition.

 - Document that the block is going to be used only once, and not called from elsewhere possibly much later. Tell the reader there's no need to remember this definition.

(Too bad [the grammar](https://docs.python.org/3/reference/grammar.html) requires a newline after a decorator; "`@immediate def`" would look nicer.)

## Notes

The main design consideration in this package is to not need `inspect`, keeping these modules simple and robust.

Since we **don't** depend on [MacroPy](https://github.com/azazel75/macropy), we provide run-of-the-mill functions and classes, not actual syntactic forms.

For more examples, see [``tour.py``](tour.py), the `test()` function in each submodule, and the docstrings of the individual features.

### On ``let`` and Python

Why no `let*`? In Python, name lookup always occurs at runtime. Python gives us no compile-time guarantees that no binding refers to a later one - in [Racket](http://racket-lang.org/), this guarantee is the main difference between `let*` and `letrec`.

Even Racket's `letrec` processes the bindings sequentially, left-to-right, but *the scoping of the names is mutually recursive*. Hence a binding may contain a lambda that, when eventually called, uses a binding defined further down in the `letrec` form. We similarly allow this.

In contrast, in a `let*` form, attempting such a definition is *a compile-time error*, because at any point in the sequence of bindings, only names found earlier in the sequence have been bound. See [TRG on `let`](https://docs.racket-lang.org/guide/let.html).

The ``lispylet`` version of `letrec` behaves slightly more like `let*` in that if the RHS is not a function, it may only refer to previous bindings. But ``lispylet.letrec`` still allows mutually recursive function definitions, hence the name.

Inspiration: [[1]](https://nvbn.github.io/2014/09/25/let-statement-in-python/) [[2]](https://stackoverflow.com/questions/12219465/is-there-a-python-equivalent-of-the-haskell-let) [[3]](http://sigusr2.net/more-about-let-in-python.html).

### Python is not a Lisp

The point behind providing `let` and `begin` is to make Python lambdas slightly more useful - which was really the starting point for this whole experiment.

The oft-quoted single-expression limitation is ultimately a herring - it can be fixed with a suitable `begin` form, or a function to approximate one.

The real problem is the statement/expression dichotomy. In Python, the looping constructs (`for`, `while`), the full power of `if`, and `return` are statements, so they cannot be used in lambdas. The expression form of `if` can be used to a limited extent (actually [`and` and `or` are sufficient for full generality](https://www.ibm.com/developerworks/library/l-prog/), but readability suffers), and functional looping (via tail recursion) is possible for short loops - where the lack of tail call elimination does not yet crash the program - but still, ultimately one must keep in mind that Python is not a Lisp.

Another factor here is that not all of Python's standard library is expression-friendly; some standard functions and methods lack return values - even though a call is an expression! For example, `set.add(x)` returns `None`, whereas in an expression context, returning `x` would be much more useful.

### Assignment syntax

Why the clunky `e.set("foo", newval)` or `e << ("foo", newval)`, which do not directly mention `e.foo`? This is mainly because in Python, the language itself is not customizable. If we could define a new operator `e.foo <op> newval` to transform to `e.set("foo", newval)`, this would be easily solved.

We could abuse `e.foo << newval`, which transforms to `e.foo.__lshift__(newval)`, to essentially perform `e.set("foo", newval)`, but this requires some magic, because we then need to monkey-patch each incoming value (including the first one when the name "foo" is defined) to set up the redirect and keep it working.

 - Methods of builtin types such as `int` are read-only, so we can't just override `__lshift__` in any given `newval`.
 - For many types of objects, at the price of some copy-constructing, we can provide a wrapper object that inherits from the original's type, and just adds an `__lshift__` method to catch and redirect the appropriate call. See commented-out proof-of-concept in [`unpythonic/env.py`](unpythonic/env.py).
 - But that approach doesn't work for function values, because `function` is not an acceptable base type to inherit from. In this case we could set up a proxy object, whose `__call__` method calls the original function (but what about the docstring and such? Is `@functools.wraps` enough?). But then there are two kinds of wrappers, and the re-wrapping logic (which is needed to avoid stacking wrappers when someone does `e.a << e.b`) needs to know about that.
 - It's still difficult to be sure these two approaches cover all cases; a read of `e.foo` gets a wrapped value, not the original; and this already violates [The Zen of Python](https://www.python.org/dev/peps/pep-0020/) #1, #2 and #3.

If we later choose go this route nevertheless, `<<` is a better choice for the syntax than `<<=`, because `let` needs `e.set(...)` to be valid in an expression context.

### Wait, no monads?

Already done elsewhere, see [PyMonad](https://bitbucket.org/jason_delaat/pymonad/) or [OSlash](https://github.com/dbrattli/OSlash) if you need them. Especially the `List` monad can be useful also in Python, e.g. to make an [`amb`](https://rosettacode.org/wiki/Amb) without `call/cc`. Compare [this solution in Ruby](http://www.randomhacks.net/2005/10/11/amb-operator/), with `call/cc`.

If you want to roll your own monads for whatever reason, there's [this silly hack](https://github.com/Technologicat/python-3-scicomp-intro/blob/master/examples/monads.py) that wasn't packaged into this; or just read Stephan Boyer's quick introduction [[part 1]](https://www.stephanboyer.com/post/9/monads-part-1-a-design-pattern) [[part 2]](https://www.stephanboyer.com/post/10/monads-part-2-impure-computations) [[super quick intro]](https://www.stephanboyer.com/post/83/super-quick-intro-to-monads) and figure it out, it's easy. (Until you get to `State` and `Reader`, where [this](http://brandon.si/code/the-state-monad-a-tutorial-for-the-confused/) and maybe [this](https://gaiustech.wordpress.com/2010/09/06/on-monads/) can be helpful.)

## Installation

Not yet available on PyPI; clone from GitHub.

### Install

Usually one of:

```
python3 setup.py install --user
```

```
sudo python3 setup.py install
```

depending on what you want.

### Uninstall

```
pip3 uninstall unpythonic
```

Must be invoked in a folder which has no subfolder called `unpythonic`, so that `pip` recognizes it as a package name (instead of a filename).

## License

2-clause [BSD](LICENSE.md).

Dynamic scoping based on [StackOverflow answer by Jason Orendorff (2010)](https://stackoverflow.com/questions/2001138/how-to-create-dynamical-scoped-variables-in-python), used under CC-BY-SA.

Core idea of `lispylet` based on [StackOverflow answer by divs1210 (2017)](https://stackoverflow.com/a/44737147), used under the MIT license.

## Python-related FP resources

- [Awesome Functional Python](https://github.com/sfermigier/awesome-functional-python), especially a list of useful libraries. Some picks:

  - [fn.py: Missing functional features of fp in Python](https://github.com/fnpy/fn.py) (actively maintained fork). Includes e.g. tail call elimination by trampolining, and a very compact way to recursively define infinite streams.

  - [more-itertools: More routines for operating on iterables, beyond itertools.](https://github.com/erikrose/more-itertools)

  - [toolz: A functional standard library for Python](https://github.com/pytoolz/toolz)

  - [funcy](https://github.com/suor/funcy/)

  - [pyrsistent: Persistent/Immutable/Functional data structures for Python](https://github.com/tobgu/pyrsistent)

- [List of languages that compile to Python](https://github.com/vindarel/languages-that-compile-to-python) including Hy, a Lisp (in the [Lisp-2](https://en.wikipedia.org/wiki/Lisp-1_vs._Lisp-2) family) that can use Python libraries.

Old, but interesting:

- [Peter Norvig (2000): Python for Lisp Programmers](http://www.norvig.com/python-lisp.html)

- [David Mertz (2001): Charming Python - Functional programming in Python, part 2](https://www.ibm.com/developerworks/library/l-prog2/index.html)

