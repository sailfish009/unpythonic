**0.14.3** (in progress; updated 21 August 2020) - *Much more robust* edition:

**New**:

- `unpythonic.test.fixtures`, a lightweight testing framework **for macro-enabled Python code**.
  - Context managers `session`, `testset`, and `catch_signals`. Various helper functions, such as `returns_normally` (for use in a `test[]`).
  - Testing macros, similar to the builtin `assert`, but with the magic of conditions and restarts: even if a test fails or errors out, further tests continue running.
    - `test[expr]`, `test[expr, message]`, `test_raises[exctype, expr]`, `test_raises[exctype, expr, message]`, `test_signals[exctype, expr]`, `test_signals[exctype, expr, message]`.
    - To help diagnosing test failures with minimum fuss, the `test[...]` macro provides an optional marker `the[expr]` to tag the interesting part inside the `test[...]` when the simplistic default capture logic doesn't capture the part you want.
      - The default is to capture the LHS when the test is a comparison, otherwise capture the whole expression. If the `the[expr]` marker is used, the `the` part is captured instead.
    - Helper macros `fail[message]` and `error[message]` for producing unconditional failures or errors. Useful e.g. if the test reached a line that should be unreachable, or when an optional dependency for some integration test is not installed.
- `callsite_filename`: return the filename from which this function is being called. Useful as a building block for debug utilities and similar.
- `equip_with_traceback`: take a manually created exception instance, equip it with a traceback. Requires Python 3.7 or later.
- `subset`: test whether an iterable is a subset of another. Convenience function.
- `allsame`: test whether all elements of an iterable are the same. Sometimes useful in writing testing code.
- `safeissubclass`: like issubclass, but if `cls` is not a class, swallow the `TypeError` and return `False`. Sometimes useful when dealing with lots of code that needs to check types dynamically.

**Non-breaking changes**:

- `@generic` and `@typed` can now decorate instance methods, class methods and static methods. This makes those *methods (OOP sense)* have *methods (generic function sense)*. Get it?
  - `self` and `cls` parameters do not participate in dispatching, and need no type annotation.
  - Beside appearing as the first positional-or-keyword parameter, the self-like parameter **must be named** one of `self`, `this`, `cls`, or `klass` to be detected by the ignore mechanism. This limitation is due to implementation reasons; while a class body is being evaluated, the context needed to distinguish a method (OOP sense) from a regular function is not yet present.
  - OOP inheritance support: when `@generic` is installed on an OOP method (instance method, or `@classmethod`), then at call time, classes are tried in [MRO](https://en.wikipedia.org/wiki/C3_linearization) order. All generic-function methods of the OOP method defined in the class currently being looked up are tested for matches first, before moving on to the next class in the MRO. (This has subtle consequences, related to in which class in the hierarchy the various generic-function methods for a particular OOP method are defined.)
  - To work with OOP inheritance, `@generic` must be the outermost decorator (except `@classmethod` or `@staticmethod`, which are essentially compiler annotations).
  - However, when installed on a `@staticmethod`, the `@generic` decorator does not support MRO lookup, because that would make no sense. See discussions on interaction between `@staticmethod` and `super` in Python: [[1]](https://bugs.python.org/issue31118) [[2]](https://stackoverflow.com/questions/26788214/super-and-staticmethod-interaction/26807879).
- To ease installation, relax version requirement of the optional MacroPy dependency to the latest released on PyPI, 1.1.0b2.
  - Once MacroPy updates, we'll upgrade; 1.1.0b2 is missing some small features we would like to use.
- Conditions: when an unhandled `error` or `cerror` occurs, the original unhandled error is now available in the `__cause__` attribute of the `ControlError** exception that is raised in this situation.
- Document named-arg bug in `curry` in the docstring. See [#61](https://github.com/Technologicat/unpythonic/issues/61). Fixing this needs a better `partial`, so for now it's a known issue.
- All of `unpythonic` itself is now tested using the new testing framework for macro-enabled code, `unpythonic.test.fixtures`. **Hence, developing `unpythonic` now requires MacroPy.** For **using** `unpythonic`, MacroPy remains strictly optional, as it will at least for the foreseeable future.

**Breaking changes**:

- *Experimental*: `@generic` no longer takes a master definition. Methods (in the generic function sense) are registered directly with `@generic`; the first method definition implicitly creates the generic function.

**Fixed**:

- Compatibility with Pythons 3.4, 3.5 and 3.7, thanks to a newly set up [CI](https://en.wikipedia.org/wiki/Continuous_integration) [workflow](https://github.com/Technologicat/unpythonic/actions) for automated multi-version testing.
- PyPy3 support: fixed crash in querying the arity of builtin functions. The fact that a function is builtin is reported slightly differently compared to CPython. See [#67](https://github.com/Technologicat/unpythonic/issues/67).
- Bug in `m()` prevented mathifying iterables that are not themselves iterators (e.g. `tuple`).
- Bugs in `s()`:
  - Respect the type of the input numbers. Particularly, if all the inputs are integers, and the sequence formula allows it, make the created sequence output integers, too.
  - In the internal function `nofterms()`, convert the output to `int` so it won't accidentally become `sympy.core.numbers.Integer` when the input is symbolic. We actually want native Python integers.
- Condition system:
  - `with handlers` catches also derived types, e.g. a handler for `Exception` now catches a signaled `ValueError`.
  - Handler lookup works correctly also for `signal(SomeExceptionClass)` without creating an instance.
  - Conditions can now inherit from `BaseException`, not only from `Exception.`
  - Uses of `issubclass` are now properly protected by a `try`/`except` when the first argument might not be a class (since in that case `issubclass` raises `TypeError`).
- `mogrify` now skips `nil`, actually making it useful for processing `ll` linked lists. Although this is technically a breaking change, the original behavior was broken, so it should not affect any existing code.

---

**0.14.2** 7 August 2020 - *"Greenspun" [edition](https://en.wikipedia.org/wiki/Greenspun%27s_tenth_rule)*:

With the arrival of [conditions and restarts](http://www.gigamonkeys.com/book/beyond-exception-handling-conditions-and-restarts.html), and a [REPL](https://en.wikipedia.org/wiki/Read%E2%80%93eval%E2%80%93print_loop) server, I think it is now fair to say `unpythonic` contains an ad-hoc, informally-specified, slow implementation of half of Common Lisp. To avoid *bug-ridden*, we have tests - but it's not entirely impossible for some to have slipped through. If you find one, please file an issue [in the tracker](https://github.com/Technologicat/unpythonic/issues).

This release welcomes the first external contribution! Thanks to @aisha-w for the much improved organization and presentation of the documentation!

**Language version**:

We target **Python 3.6**. Now we test on both **CPython** and **PyPy3**.

Rumors of the demise of Python 3.4 support are exaggerated. While the testing of `unpythonic` has moved to 3.6, there neither is nor will there be any active effort to intentionally drop 3.4 support until `unpythonic` reaches 0.15.0.

That is, support for 3.4 will likely be dropped with the arrival of the next batch of breaking changes. The current plan is visible in the roadmap [as the 0.15.0 milestone](https://github.com/Technologicat/unpythonic/milestone/1).

If you're still stuck on 3.4 and find something in the latest `unpythonic` 0.14.x doesn't work there, please file an issue. (Support for 0.14.x will end once 0.15 is released, but not before.)

**New**:

- Improve organization and presentation of documentation (#28).
- Macro README: Emacs syntax highlighting for `unpythonic.syntax` and MacroPy.
- **Resumable exceptions**, a.k.a. *conditions and restarts*. One of the famous killer features of Common Lisp. Drawing inspiration from [python-cl-conditions](https://github.com/svetlyak40wt/python-cl-conditions/) by Alexander Artemenko. See `with restarts` (Common Lisp equivalent: `RESTART-CASE`), `with handlers` (`HANDLER-BIND`), `signal` (`SIGNAL`), `invoke` (`INVOKE-RESTART`). Many convenience forms are also exported; see `unpythonic.conditions` for a full list. For an introduction to conditions, see [Chapter 19 in Practical Common Lisp by Peter Seibel](http://www.gigamonkeys.com/book/beyond-exception-handling-conditions-and-restarts.html).
- **REPL server** and client. Interactively hot-patch your running Python program! Another of the famous killer features of Common Lisp. The server is daemonic, listening for connections in a background thread. (Don't worry, it's strictly opt-in.) See `unpythonic.net.server` and `unpythonic.net.client`.
- *Batteries for network programming*:
  - `unpythonic.net.msg`: A simplistic message protocol for sending message data over a stream-based transport (such as TCP).
  - `unpythonic.net.ptyproxy`: Proxy between a Linux [PTY](https://en.wikipedia.org/wiki/Pseudoterminal) and a network socket. Useful for serving terminal utilities over the network. This doesn't use `pty.spawn`, so Python libraries that expect to run in a terminal are also welcome. See `unpythonic.net.server` for a usage example.
  - `unpythonic.net.util`: Miscellaneous small utilities.
- `fix`: Break infinite recursion cycles (for pure functions). Drawing inspiration from original implementations by [Matthew Might](http://matt.might.net/articles/parsing-with-derivatives/) and [Per Vognsen](https://gist.github.com/pervognsen/8dafe21038f3b513693e).
- More batteries for itertools:
  - `fixpoint`: Arithmetic fixed-point finder (not to be confused with `fix`).
  - `within`: Yield items from iterable until successive iterates are close enough (useful with [Cauchy sequences](https://en.wikipedia.org/wiki/Cauchy_sequence)).
  - `chunked`: Split an iterable into constant-length chunks.
  - `lastn`: Yield the last `n` items from an iterable.
  - `pad`: Extend iterable to length `n` with a `fillvalue`.
  - `interleave`: For example, `interleave(['a', 'b', 'c'], ['+', '*']) --> ['a', '+', 'b', '*', 'c']`. Interleave items from several iterables, slightly differently from `zip`.
  - `find`: From an iterable, get the first item matching a given predicate. Convenience function.
  - `powerset`: Compute the power set (set of all subsets) of an iterable. Works also for infinite iterables.
  - `CountingIterator`: Count how many items have been yielded, as a side effect.
  - `slurp`: Extract all items from a `queue.Queue` (until it is empty) into a list, returning that list.
  - `map`: Curry-friendly thin wrapper for the builtin `map`, making it mandatory to specify at least one iterable.
  - `running_minmax`, `minmax`: Extract both min and max in one pass over an iterable. The `running_` variant is a scan and returns a generator; the just-give-me-the-final-result variant is a fold.
- `ulp`: Given a float `x`, return the value of the unit in the last place (the "least significant bit"). At `x = 1.0`, this is the [machine epsilon](https://en.wikipedia.org/wiki/Machine_epsilon), by definition of the machine epsilon.
- `partition_int`: split a small positive integer, in all possible ways, into smaller integers that sum to it.
- `dyn` now supports rebinding, using the assignment syntax `dyn.x = 42`. To mass-update atomically, see `dyn.update`.
- `box` now supports `.set(newvalue)` to rebind (returns the new value as a convenience), and `unbox(b)` to extract contents. Syntactic sugar for rebinding is `b << newvalue` (where `b` is a box).
- `ThreadLocalBox`: A box with thread-local contents. It also holds a default object, which is used when a particular thread has not placed any object into the box.
- `Some`: An immutable box. Useful for optional fields; tell apart the presence of a `None` value (`Some(None)`) from the absence of a value (`None`).
- `Shim`: A shim holds a `box` or a `ThreadLocalBox`, and redirects attribute accesses to whatever object is currently in the box. The point is that the object in the box can be replaced with a different one later, while keeping the attribute proxy in place. One use case is to redirect standard output only in particular threads.
- `islice` now supports negative start and stop. (**Caution**: no negative step; and it must consume the whole iterable to determine where it ends, if at all.)
- `async_raise`: Inject KeyboardInterrupt into an arbitrary thread. (*CPython only*.)
- `resolve_bindings`: Get the parameter bindings a given callable would establish if it was called with the given args and kwargs. This is mainly of interest for implementing memoizers, since this allows them to see (e.g.) `f(1)` and `f(a=1)` as the same thing for `def f(a): pass`.
- `Singleton`: a base class for singletons that interacts properly with `pickle`. The pattern is slightly pythonified; instead of silently returning the same instance, attempting to invoke the constructor while an instance already exists raises `TypeError`. This solution separates concerns better; see [#22](https://github.com/Technologicat/unpythonic/issues/22).
- `sym`: a lispy symbol type; or in plain English: a lightweight, human-readable, process-wide unique marker, that can be quickly compared to another such marker by object identity (`is`). These named symbols are *interned*. Supplying the same name to the constructor results in receiving the same object instance. Symbols survive a `pickle` roundtrip.
- `gensym`: a utility to create a new, unique *uninterned* symbol. Like the pythonic idiom `nonce = object()`, but with a human-readable label, and with `pickle` support. Object identity of gensyms is determined by an UUID, generated when the symbol is created. Gensyms also survive a `pickle` roundtrip.

**Experimental features**:

Each experimental feature is a provisional proof-of-concept, usually lacking battle-testing and polish. Details may still change in a backwards-incompatible way, or the whole feature may still be removed. Do not depend on it in production!

- **Multiple dispatch**. The `generic` decorator makes a generic function with multiple dispatch. Arity and type annotations determine which method of the generic function a specific call of the function is dispatched to.
  - This essentially allows replacing the `if`/`elif` dynamic type checking boilerplate of polymorphic functions with type annotations on the function parameters, with support for features from the `typing` stdlib module.
  - Inspired by the [multi-methods of CLOS](http://www.gigamonkeys.com/book/object-reorientation-generic-functions.html) (the Common Lisp Object System), and the [generic functions of Julia](https://docs.julialang.org/en/v1/manual/methods/).
- `typed`: The little sister of the `generic` decorator. Restrict allowed argument types to one specific combination only.
- `isoftype`: The big sister of `isinstance`. Type check a value against a type specification at run time, with support for many (but not all) features from the [`typing`](https://docs.python.org/3/library/typing.html) module. This is the machinery that powers `@generic` and `@typed`.
  - If you need a run-time type checker for serious general use, consider the [`typeguard`](https://github.com/agronholm/typeguard) library.

**Non-breaking changes**:

- `setescape`/`escape` have been renamed `catch`/`throw`, to match the standard terminology in the Lisp family. **The old nonstandard names are now deprecated, and will be removed in 0.15.0.**
- The parameters of `raisef` are now more pythonic, just the object `exc` and an optional keyword-only `cause`. **Old-style parameters are now deprecated, and will be removed in 0.15.0.** See [#30](https://github.com/Technologicat/unpythonic/issues/30).
- `runpipe` and `getvalue` are now both replaced by a single unified name `exitpipe`. This is just a rename, with no functionality changes. **The old names are now deprecated, and will be removed in 0.15.0.**
- Accessing the `.x` attribute of a `box` directly is now deprecated. It does not work with `ThreadLocalBox`, which must handle things differently due to implementation reasons. Instead, use the API, which works for both types of boxes. `b << newvalue` (syntactic sugar) or `b.set(newvalue)` sends a different object into the box, and `unbox(b)` (syntactic sugar) or `b.get()` retrieves the current value.
- The `dbg[]` macro now works in the REPL, too. See [#12](https://github.com/Technologicat/unpythonic/issues/12).
- The `namedlambda` block macro now also names lambdas that are:
  - Passed as a named argument of a function call, as in ``foo(f=lambda ...: ...)``; or
  - Inside a dictionary literal, with a literal string key, as in ``{"f": lambda ...: ...}``. See [#40](https://github.com/Technologicat/unpythonic/issues/40).
- Move macro documentation to `doc/macros.md`. (Was `macro_extras/README.md`.)
- Add contribution guidelines, `HACKING.md`.

**Fixed**:

- Fix initialization crash in `lazyutil` if MacroPy is not installed.
- Fix bug in `identity` and `const` with zero args ([#7](https://github.com/Technologicat/unpythonic/issues/7)).
- Use standard Python semantics for negative indices ([#6](https://github.com/Technologicat/unpythonic/issues/6)).
- Escape continuation analysis in `unpythonic.syntax.util` now interprets also the literal name `throw` as invoking an escape continuation.
- Fix pickling of `frozendict` ([#55](https://github.com/Technologicat/unpythonic/issues/55)).
- Fix spurious cache misses in memoizers ([#26](https://github.com/Technologicat/unpythonic/issues/26)). The bug affected `memoize`, `gmemoize`, `fix` and `fixtco`.

---

**0.14.1** 9 June 2019 - *Retrofuturistic edition*:

**Language version**:

- Support Python 3.6. First released in 2016, supported until 2021, most distros should have it by now.
- This will be the final release that supports Python 3.4; upstream support for 3.4 ended in March 2019.

**New**:

- ``Popper``, a pop-while iterator.
- ``window``, a length-n sliding window iterator for general iterables.
- ``autoref[]`` can now be nested.
- ``dbg[]`` now supports also an expression variant, customizable by lexically assigning ``dbgprint_expr``. See the README on macros for details.

**Bugfixes**:

- Fix crash when SymPy or mpmath are not installed.
- ``mogrify`` is now part of the public API, as it should have been all along.
- Docs: Mention the ``mg`` function in the README.

**Non-breaking changes**:

- Future-proof ``namelambda`` for Python 3.8.
- Docs: ``dbg[]`` is now listed as a convenience feature in the README.

---

**0.14.0** 18 March 2019 - *"Dotting the t's and crossing the i's" edition*:

**Bugfixes**:

 - ``setup.py``: macros are not zip safe, because ``ZipImporter`` fails to return source code for the module and MacroPy needs that.
 - fix splicing in the ``do[]`` macro; ``ExpandedDoView`` should now work correctly
 - fix lambda handling in the ``lazify`` macro
 - fix ``dict_items`` handling in ``mogrify`` (fixes the use of the ``curry`` macro with code using ``frozendict``)

**New**:

 - ``roview``: a read-only view into a sequence. Behaves mostly the same as ``view``, but has no ``__setitem__`` or ``reverse``.
 - ``mg``: a decorator to mathify a gfunc, so that it will ``m()`` the generator instances it makes.
 - The ``do[]`` macro now supports ``delete[name]`` to delete a local variable previously created in the same do-expression using ``local[name << value]``.
 - ``envify`` block macro, to make formal parameters live in an unpythonic ``env``.
 - ``autoref`` block macro, to implicitly reference attributes of an object (for reading only).

**Breaking changes**:

 - The ``macropy3`` bootstrapper now takes the ``-m`` option; ``macropy3 -m somemod``, like ``python3 -m somemod``. The alternative is to specify a filename positionally; ``macropy3 somescript.py``, like ``python3 somescript.py``. In either case, the bootstrapper will import the module in a special mode that pretends its ``__name__ == '__main__'``, to allow using the pythonic conditional main idiom also in macro-enabled code.
 - The constructor of the writable ``view`` now checks that the input is not read-only (``roview``, or a ``Sequence`` that is not also a ``MutableSequence``) before allowing creation of the writable view.
 - ``env`` now checks finalization status also when deleting attrs (a finalized ``env`` cannot add or delete bindings)

**Non-breaking improvements**:

 - ``env`` now provides also the ``collections.abc.MutableMapping`` API.
 - The ``tco`` macro now skips nested ``continuations`` blocks (to allow [Lispython](https://github.com/Technologicat/pydialect/tree/master/lispython) in [Pydialect](https://github.com/Technologicat/pydialect) to support ``continuations``).
 - ``setup.py`` now installs the ``macropy3`` bootstrapper.

---

**0.13.1** 1 March 2019 - *"Maybe a slice?" [edition](https://en.wikipedia.org/wiki/Everybody%27s_Golf_4)*

**New**:

 - `view`: writable, sliceable view into a sequence. Use like `view(lst)[::2]`. Can be nested (i.e. sliced again). Any access (read or write) goes through to the original underlying sequence. Can assign a scalar to a slice à la NumPy. Stores slices, not indices; works also if the length of the underlying sequence suddenly changes.
 - `islice`: slice syntax support for `itertools.islice`, use like `islice(myiterable)[100:10:2]` or `islice(myiterable)[42]`. (It's essentially a curried function, where the second step uses the subscript syntax instead of the function call syntax.)
 - `prod`: like `sum`, but computes the product. A missing battery.
 - `iindex`: like `list.index`, but for iterables. A missing battery. (Makes sense mostly for memoized input.)
 - `inn(x, iterable)`: contains-check (`x in iterable`) for monotonic infinite iterables, with [automatic](http://wiki.c2.com/?LazinessImpatienceHubris) termination.
 - `getattrrec`, `setattrrec` (**rec**ursive): access underlying data in an onion of wrappers.
 - `primes` and `fibonacci` generators, mainly intended for testing and usage examples.
 - ``SequenceView`` and ``MutableSequenceView`` abstract base classes; ``view`` is a ``MutableSequenceView``.

**Breaking changes**:

 - The `fup[]` utility macro to functionally update a sequence **is gone and has been replaced** by the `fup` utility function, with slightly changed syntax to accommodate. New syntax is like `fup(lst)[3:17:2] << values`. (This is a two-step curry utilizing the subscript and lshift operators.)
 - `ShadowedSequence`, and hence also `fupdate`, now raise the semantically more appropriate `IndexError` (instead of the previous `ValueError`) if the replacement sequence is too short.
 - `namelambda` now returns a modified copy; the original function object is no longer mutated.

**Non-breaking improvements**:

 - `ShadowedSequence` now supports slicing (read-only), equality comparison, `str` and `repr`. Out-of-range access to a single item emits a meaningful error, like in `list`.
 - `env` and `dyn` now provide the `collections.abc.Mapping` API.
 - `cons` and friends: `BinaryTreeIterator` and `JackOfAllTradesIterator` now support arbitarily deep cons structures.

---

**0.13.0** 25 February 2019 - *"I'll evaluate this later" edition*:

**New**:

 - ``lazify`` macro: call-by-need for Python (a.k.a. lazy functions, like in Haskell)
 - ``frozendict``: an immutable dictionary
 - ``mogrify``: in-place ``map`` for mutable containers
 - ``timer``: a context manager for performance testing
 - `s`: create lazy mathematical sequences. For example, `s(1, ...)`, `s(1, 2, ...)`, `s(1, 2, 4, ...)` and `s(1, 2, ...)**2` are now valid Python. Regular function, no macros.
 - `m`: endow any iterable with infix math support. (But be aware that after that, applying an operation meant for general iterables drops the math support; to restore it, `m(result)` again.)
 - The ``unpythonic.llist`` module now provides ``JackOfAllTradesIterator`` that understands both trees and linked lists (with some compromises).
 - ``nb`` macro: a silly ultralight math notebook.

**Breaking changes**:

 - ``dyn``: the ``asdict`` and ``items`` methods now return a live view.
 - The mutable single-item container ``Box`` and its data attribute ``value`` have been renamed to ``box`` and ``x``, respectively.
 - ``namedlambda`` macro: Env-assignments are now processed lexically, just like regular assignments. Added support for let-bindings.
 - ``curry`` macro: The special mode for uninspectables is now enabled lexically within the ``with curry`` block. Also, manual uses of the ``curry`` decorator (on both ``def`` and ``lambda``) are now detected, and in such cases the macro now skips adding the ``curry`` decorator.

**Non-breaking improvements**:

 - ``namelambda`` now supports renaming any function object, and also multiple times.
 - The single-item special binding syntax is now supported also by the bindings block of the ``dlet``, ``dletseq``, ``dletrec``, ``blet``, ``bletseq`` and ``bletrec`` macros.

---

**0.12.0** 9 January 2019 - *"[Metamagical](https://en.wikipedia.org/wiki/Metamagical_Themas) engineering" edition*:

*What does "metamagical" mean? To me, it means "going one level beyond magic". There is an ambiguity here: on the one hand, the word might mean "ultramagical" - magic of a higher order - yet on the other hand, the magical thing about magic is that what lies behind it is always nonmagical. That's metamagic for you!*
  --Douglas R. Hofstadter, *On Self-Referential Sentences* (essay, 1981)

**New**:

 - Alternative, haskelly ``let`` syntax ``let[((x, 2), (y, 3)) in x + y]`` and ``let[x + y, where((x, 2), (y, 3))]``
   - Supported by all ``let`` forms: ``let``, ``letseq``, ``letrec``, ``let_syntax``, ``abbrev``
 - When making just one binding, can now omit outer parentheses in ``let``: ``let(x, 1)[...]``, ``let[(x, 1) in ...]``, ``let[..., where(x, 1)]``
 - ``unpythonic.misc.Box``: the classic rackety single-item mutable container
 - Many small improvements to documentation

**Breaking changes**:

 - New, perhaps more natural ``call_cc[]`` syntax for continuations, replaces earlier ``with bind[...]``
   - Conditional continuation capture with ``call_cc[f() if p else None]``
   - ``cc`` parameter now added implicitly, no need to declare explicitly unless actually needed (reduces visual noise in client code)
 - Local variables in a ``do`` are now declared using macro-expr syntax ``local[x << 42]``, looks more macropythonic
 - Silly ``(lambda)`` suffix removed from names of named lambdas (to detect them in client code, it's enough that ``isinstance(f, types.LambdaType)``)

---

**0.11.1** 22 November 2018 - *"Cleaning up, vol. 2" edition*:

**Enhancements**:

- Create a proper decorator registry for the syntax machinery.
  - Can now register priorities for custom decorators to tell the syntax system about their correct ordering (for ``sort_lambda_decorators``, ``suggest_decorator_index``).
  - Register priorities for (some of) unpythonic's own decorators using this new system, replacing the old hardcoded decorator registry.
  - Now lives in ``unpythonic.regutil``; used only by the syntax subsystem, but doesn't require MacroPy just to start up.
- Try to determine correct insertion index for ``trampolined`` and ``curry`` decorators in macros that insert them to ``decorator_list`` of ``FunctionDef`` nodes (using any already applied known decorators as placement hints, [like a programmer would](http://wiki.c2.com/?LazinessImpatienceHubris)).
- ``namedlambda``: recognize also decorated lambdas, and calls to ``curry`` where the last argument is a lambda (useful for ``looped_over`` et al.).

**Breaking change**:

- Remove the special jump target ``SELF``.
  - Was always a hack; no longer needed now that v0.11.0 introduced the general solution: the ``withself`` function that allows a lambda to refer to itself anywhere, not just in a ``jump``.
  - Now the whole thing is easier to explain, so likely a better idea ([ZoP](https://www.python.org/dev/peps/pep-0020/) §17, 18).

---

**0.11.0** 15 November 2018 - *"Spring cleaning in winter" edition*:

New:

- Add @callwith: freeze arguments, choose function later
- Add withself: allow a lambda to refer to itself
- Add let_syntax: splice code at macro expansion time
- Add quicklambda: block macro to combo our blocks with MacroPy's quick_lambda
- Add debug option to MacroPy bootstrapper

Enhancements:

- prefix macro now works together with let and do

Bugfixes:

- detect TCO'd lambdas correctly (no longer confused by intervening FunctionDef nodes with TCO decorators)
- scoping: detect also names bound by For, Import, Try, With

Breaking changes:

- Rename dynscope --> dynassign; technically dynamic assignment, not scoping
- Rename localdef --> local; shorter, more descriptive
- scanr now returns results in the order computed (**CAUTION**: different from Haskell)
- simple_let, simple_letseq --> let, letseq in unpythonic.syntax.simplelet
- cons now prints pythonically by default, to allow eval; use .lispyrepr() to get the old output
- Remove separate dynvar curry_toplevel_passthrough; expose curry_context instead

Other:

- Reorganize source tree, tests now live inside the project
- Pythonize runtests, no more bash script
- Add countlines Python script to estimate project size

---

**0.10.4** 29 October 2018 - *"573 combo!" edition[*](http://www.dancedancerevolution.wikia.com/wiki/573)*:

- new: macro wrappers for the let decorators
- fix: trampolined() should go on the outside even if the client code manually uses curry()
- enh: improve tco, fploop combo
- enh: improve lexical scoping support

---

**0.10.3** 25 October 2018 - *"Small fixes" edition*:

- enh: ``curry`` macro now curries also definitions (``def``, ``lambda``), not only calls
- fix: spurious recomputation bug in ``do[]``
- update and fix READMEs and docstrings

---

**0.10.2** 24 October 2018 - *"Just a few more things" edition*:

Bugfixes:

- Arities:
  - Compute arities of methods correctly
  - Workaround for some builtins being uninspectable or reporting incorrect arities
- Macros:
  - An implicit ``curry(f)`` should call ``f`` also if no args
  - Fix missing ``optional_vars`` in manually created ``withitem`` nodes

---

**0.10.1** 23 October 2018 - *["Just one more thing"](https://drmarkgriffiths.wordpress.com/2016/08/08/just-one-more-thing-the-psychology-of-columbo/) edition*:

- ``continuations``: create continuation using same node type (``FunctionDef`` or ``AsyncFunctionDef``) as its parent function
- ``autoreturn``: fix semantics of try block
- fix docstring of tco

---

**0.10.0** 23 October 2018 - *"0.10.0 is more than 0.9.∞" edition*:

- Add more macros, notably ``continuations``, ``tco``, ``autoreturn``
- Polish macros, especially their interaction
- Remove old exception-based TCO, rename ``fasttco`` to ``tco``

---

**0.9.2** 9 October 2018 - *"Through the looking glass" edition*:

 - new `multilambda` block macro: supercharge regular Python lambdas, contained lexically inside the block, with support for multiple expressions and local variables. Use brackets to denote a multi-expression body.
 - new `fup` macro providing more natural syntax for functional updates; allows using slice syntax.
 - upgrade: the `let` macros can now optionally have a multi-expression body. To enable, wrap the body in an extra set of brackets.
 - remove the 0.9.0 multilambda `λ`; brittle and was missing features.

The macros implement the multi-expression bodies by inserting a `do`; this introduces an internal-definition context for local variables. See its documentation in the macro_extras README for usage.

The macro_extras README now includes a table of contents for easy browsability.

---

**0.9.0** 5 October 2018 - *["Super Syntactic Fortress MACROS"](https://en.wikipedia.org/wiki/Super_Dimension_Fortress_Macross) edition*:

- **Macros!** New module `unpythonic.syntax`, adding syntactic macros for constructs where this improves usability. See [`macro_extras`](macro_extras/) for documentation.
  - Notable macros include `curry` (automatic currying for Python) and `cond` (multi-branch conditional expression, usable in a lambda), and macro variants of the `let` constructs (no boilerplate).
  - As of this writing, requires the [latest MacroPy3](https://github.com/azazel75/macropy) from git HEAD.
  - Not loaded by default. To use, `from unpythonic.syntax import macros, ...`.
- Include generic MacroPy3 bootstrapper for convenience, to run macro-enabled Python programs.
- Fix bug in let constructs: should require unique names in the same `let`/`letrec`.
- Fix bug in `unpythonic.fun.apply`.

---

**0.8.8** 25 September 2018 - *"More [spicy](https://github.com/Technologicat/spicy)" edition*:

Changes:

- ``curry``: by default, ``TypeError`` if args remaining when exiting top-level curry context
  - add dynvar ``curry_toplevel_passthrough`` to switch the error off
- ``rotate`` now conceptually shifts the arg slots, not the values; this variant seems easier to reason about.
- accept just tuple (not list) as the pythonic multiple-return-values thing in ``curry``, ``compose``, ``pipe``

New:

- add ``make_dynvar``, to set a default value for a dynamic variable. Eliminates the need for ``if 'x' in dyn`` checks.
- as an optional extra, add a [MacroPy3](https://github.com/azazel75/macropy) based autocurry macro, which automatically curries all function calls that lexically reside in a ``with curry`` block. (Make your Python look somewhat like Haskell.)

Bugfixes/optimizations:

- ``nth``: fix off-by-one bug
- ``dyn``: skip pushing/popping a scope if no bindings given

---

**0.8.7** 24 September 2018 - *"More iterable" edition*:

Changes:

 - `scanr` now syncs the left ends of multiple inputs, as it should.
 - robustness: add a typecheck to `ShadowedSequence.__init__`
 - rename: for consistency with `rscanl`, `rfoldl`, the new names of *sync right ends of multiple inputs, then map/zip from the right*, are `rmap`, `rzip`.
 - `llist`, `lreverse` are now more ducky/pythonic.

New:

 - add `rscanl`, `rscanl1`, `rfoldl`, `rreducel`: reverse each input, then left-scan/left-fold. This approach syncs the right ends if multiple inputs.
 - add `mapr`, `zipr` (map-then-reverse): sync left ends of multiple inputs, then map/zip from the right.
 - add convenience function `rev`: try `reversed(...)`, if `TypeError` then `reversed(tuple(...))`
 - add `butlast`, `butlastn`, `partition`

---

**0.8.6** 20 September 2018 - *"Adding in the missing parts" edition*:

New features:

 - add `unfold`, `unfold1`: generate a sequence corecursively
 - add memoization for iterables (`imemoize`, `fimemoize`)

Enhancements:

 - `call` now accepts also args (see docstring)
 - gtco: allow tail-chaining into any iterable
 - document new features in README (also those from 0.8.5)

Bugfixes:

 - fix bugs in gtco
   - strip trampolines correctly in nested generator-TCO chains
   - fix handling of generator return values

---

**0.8.5** 19 September 2018 - *"Liberté, égalité, fraternité" edition*:

 - add `gtrampolined`: TCO (tail chaining) for generators
 - add `gmemoize`: memoization for generators
 - bring convenience features of `dyn` to parity with `env`

---

**0.8.4** 18 September 2018 - *["The hunt for missing operators"](https://en.wikipedia.org/wiki/The_Hunt_for_Red_October_(film)) edition*:

 - Parameterize scan and fold; can now terminate on longest input
 - Add `map_longest`, `mapr_longest`, `zipr_longest`
 - `unpack` is now curry-friendly

Technical enhancements:

 - refactor `unpythonic.it` to use `itertools` where possible
 - remove unnecessary conversions from iterator to generator

---

**0.8.3** 18 September 2018 - *"I have always wanted to code in Listhonkell" edition*:

 - Add `scanl`, `scanr`: lazy partial fold (a.k.a. accumulate) that returns a generator yielding intermediate results.
   - Also provided are `scanl1`, `scanr1` variants with one input sequence and optional init.
 - Add `iterate`: return an infinite generator yielding `x`, `f(x)`, `f(f(x))`, ...
   - 1-in-1-out (`iterate1`) and n-in-n-out (`iterate`) variants are provided. The n-in-n-out variant unpacks each result to the argument list of the next call.

For usage examples see `test()` in [it.py](unpythonic/it.py).

---

**0.8.2** 17 September 2018

New features:

 - Add currying compose functions and currying pipe (names suffixed with ``c``)

Enhancements:

 - Improve reversing support in linked lists:
   - Linked lists now support the builtin ``reversed`` (by internally building a reversed copy)
   - ``llist`` just extracts the internal reversed copy when the input is ``reversed(some_ll)``
 - Prevent stacking curried wrappers in ``curry``
 - More logical naming for the ``compose`` variants.
   - The first suffix, if present, is either ``1`` for one-arg variants, or ``c`` for the new currying variants.
   - The ``i`` suffix for iterable input always goes last.

---

**0.8.1** 14 September 2018

New feature:

 - Add a toy nondeterministic evaluator `forall`; see `unpythonic.amb` module

Enhancements:

 - Improve curry; see updated examples in README
 - cons structures are now pickleable
 - `unpythonic.llist` no longer depends on `unpythonic.tco`

---

**0.8.0** 12 September 2018

Features:

 - `unpythonic.it`: batteries for itertools (new)
 - `unpythonic.fun`: batteries for functools (significant changes)
 - m-in-n-out for pipes and function composition (new)
 - `unpythonic.fup`: functionally update sequences and mappings (new)
 - Load `unpythonic.llist` by default (easier, no special cases for the user)

Bugfix:

 - `curry` with passthrough: use up all kwargs at the first step which got too many positional arguments (since no simple reasonable way to decide to which later application they would belong)

---

**0.7.0** 4 September 2018

 - Add batteries for functools: `unpythonic.fun`
 - Add `cons` and friends: `unpythonic.llist` (not loaded by default; depends on `unpythonic.tco`)
 - Bugfix: `rc.py` was missing from the distribution, breaking TCO

---

**0.6.1** 29 August 2018 (hotfix for 0.6.0)

Bugfix:

 - Catch `UnknownArity` in all modules that use `unpythonic.arity.arity_includes()`.

---

**0.6.0** 29 August 2018

New and improved sequencing constructs.

 - Rename the v0.5.1 `do` --> `pipe`
 - Add `piped`, `lazy_piped` for shell-like pipe syntax
 - Add a new `do`: an improved `begin` that can name intermediate results

---

**0.5.1** 13 August 2018

 - Catch more errors in client code:
   - Validate arity of callable value in `letrec` (both versions)
   - Validate callability and arity of body in all `let` constructs
   - In `env`, require name to be an identifier even when subscripting
 - Add flag to `enable_fasttco()` to be able to switch it back off (during the same run of the Python interpreter)
 - Internal enhancement: add unit tests for `env`

---

**0.5.0** 10 August 2018

- Make the TCO implementation switchable at run time, see `enable_fasttco()`.
- Default to the slower exception-based TCO that has easier syntax.

---

**0.4.3** 9 August 2018

- Print a warning for unclaimed TCO jump instances (to help detect bugs in client code)

---

**0.4.2** 6 August 2018 (hotfix for 0.4.1)

- fix install bug

---

**0.4.1** 6 August 2018 (hotfix for 0.4.0)

- Export `unpythonic.misc.pack`
- Update description for PyPI

---

**0.4.0** 6 August 2018

- First version published on PyPI
- Add `@breakably_looped`, `@breakably_looped_over`
- Rename `@immediate` to `@call`; maybe the most descriptive short name given `call/ec` and similar.

---

**0.3.0** 6 August 2018

- refactor looping constructs into `unpythonic.fploop`
- add exception-based alternative TCO implementation
- add `raisef`
- change API of `escape` to perform the `raise` (simplifies trampoline, improves feature orthogonality)

---

**0.2.0** 3 August 2018

- add `@call/ec`
- add `arity` utilities
- rename `@loop` -> `@looped`; now `loop` is the magic first positional parameter for the loop body
- add `@looped_over`
- unify `let` behavior between the two implementations
- make `@trampolined` preserve docstrings
- `@setescape`: parameter should be named `tags` since it accepts a tuple
- improve README

---

**0.1.0** 30 July 2018

Initial release.
