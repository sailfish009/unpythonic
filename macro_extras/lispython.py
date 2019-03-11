# -*- coding: utf-8 -*-
"""Lispython: the love child of Python and Scheme.

Powered by Pydialect and unpythonic.

This module is the dialect definition, invoked by ``dialects.DialectFinder``
when it detects a lang-import that matches the module name of this module.

This dialect is implemented in MacroPy.

**Features**:

    - Fully automatic TCO in both ``def`` and ``lambda``
    - Implicit ``return`` in any tail position, like in Lisps
    - ``lambda`` allows multiple expressions (use brackets)
    - Lambdas are named automatically (whenever the machinery can figure out
      an appropriate name)
    - As builtins, all ``let[]`` constructs and ``do[]``, ``do0[]`` from
      ``unpythonic.syntax``

For detailed documentation, see the module ``unpythonic.syntax`` and the macros
``tco``, ``autoreturn``, ``multilambda``, ``namedlambda`` and ``let`` therein.
The multi-expression lambda syntax uses ``do[]``, see its documentation for
details.

Also, in Lispython the following functions are considered builtins:

    - ``cons``, ``car``, ``cdr``, ``ll``, ``llist``
    - ``prod`` (the obvious cousin of ``sum``)

For more, import from  ``unpythonic``, the standard library of Lispython
(on top of what Python itself already provides).

**What Lispython is**

The goal of the Lispython dialect is to fix some glaring issues that hamper
Python when viewed from a Lisp/Scheme perspective. We take the approach of
a relatively thin layer of macros (and underlying functions that implement
the actual functionality), minimizing magic as far as reasonably possible.

Performance is only a secondary concern; performance-critical parts fare better
at the other end of the wide spectrum, with Cython. Lispython is for the
remaining 80% of the code, where the bottleneck is human developer time.

    https://en.wikipedia.org/wiki/Wide-spectrum_language
    https://en.wikipedia.org/wiki/Pareto_principle
    http://cython.org/

The dialect aims at production quality.

**Why extend Python?**

Racket is an excellent Lisp, especially with sweet, sweet expressions, not to
mention extremely pythonic. The word is *rackety*; the syntax of the language
comes with an air of Zen minimalism (as perhaps expected of a descendant of
Scheme), but the focus on *batteries included* and understandability are
remarkably similar to the pythonic ideal. Racket even has an IDE (DrRacket)
and an equivalent of PyPI, and the documentation is simply stellar.

    https://docs.racket-lang.org/sweet/
    https://sourceforge.net/projects/readable/
    https://srfi.schemers.org/srfi-110/srfi-110.html
    https://srfi.schemers.org/srfi-105/srfi-105.html
    https://racket-lang.org/

Python, on the other hand, has a slight edge in usability to the end-user
programmer, and importantly, a huge ecosystem of libraries, second to ``None``.
Python is where science happens (unless you're in CS). Python is an almost-Lisp
that has delivered on the productivity promise of Lisp.

    http://paulgraham.com/icad.html

However, in certain other respects, Python the base language leaves something
to be desired, if you have been exposed to Racket (or Haskell, but that's a
different story). Writing macros is harder due to the irregular syntax, but
thankfully MacroPy already exists, and any set of macros only needs to be
created once.

Practicality beats purity: hence, fix the minor annoyances that would otherwise
quickly add up, and reap the benefits of both worlds. If Python is software
glue, Lispython is an additive that makes it flow better.

**Note**

For PG's accumulator puzzle even Lispython can do no better than this
let-over-lambda::

    foo = lambda n0: let[(n, n0) in
                         (lambda i: n << n + i)]
    f = foo(10)
    f(1) # 11
    f(1) # 12

which still sets up a separate place for the accumulator. The modern pure
Python solution avoids that, but needs many lines::

    def foo(n):
        def accumulate(i):
            nonlocal n
            n += i
            return n
        return accumulate
    f = foo(10)
    f(1) # 11
    f(1) # 12

The problem is that assignment to a lexical variable (including formals) is a
statement in Python. If we abbreviate ``accumulate`` as a lambda, it needs a
``let`` environment to write in (to use unpythonic's expression-assignment).

But see ``envify`` in ``unpythonic.syntax``, which allows this::

    from unpythonic.syntax import macros, envify

    with envify:
        def foo(n):
            return lambda i: n << n + i
        f = foo(10)
        f(1) # 11
        f(1) # 12

(This is also valid Lispython, and in Lispython you can omit the ``return``.
The ``envify`` macro is designed to run after the macros implicitly invoked by
the Lispython dialect.)

``envify`` may be made part of the Lispython dialect definition later, but
first it needs testing to decide whether this particular, perhaps rarely used,
feature is worth the performance hit.

**CAUTION**

No instrumentation exists (or is even planned) for the Lispython layer; you'll
have to use regular Python tooling to profile, debug, and such. The layer
should be thin enough for this not to be a major problem in practice.
"""

from macropy.core.quotes import macros, q, name

# TODO: The dialect finder imports us, so do not from-import to avoid dependency loop.
import dialects  # TODO: a proper pydialect package

def ast_transformer(module_body):
    with q as template:
        from unpythonic.syntax import macros, tco, autoreturn, \
                                      multilambda, quicklambda, namedlambda, \
                                      let, letseq, letrec, do, do0, \
                                      dlet, dletseq, dletrec, \
                                      blet, bletseq, bletrec, \
                                      let_syntax, abbrev, \
                                      cond
        # auxiliary syntax elements for the macros
        from unpythonic.syntax import local, where, block, expr, f, _
        from unpythonic import cons, car, cdr, ll, llist, prod
        with namedlambda:  # MacroPy #21 (nontrivial two-pass macro; seems I didn't get the fix right)
            with autoreturn, quicklambda, multilambda, tco:
                name["__paste_here__"]
    return dialects.splice_ast(module_body, template, "__paste_here__")

def rejoice():
    s = \
"""**Schemers rejoice!**::

    Multiple musings mix in a lambda,
    Lament no longer the lack of let.
    Languish no longer labelless, lambda,
    Linked lists cons and fold.
    Tail-call into recursion divine,
    The final value always provide."""
    print(s)
    return s
