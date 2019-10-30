# Unpythonic: Python meets Lisp and Haskell

In the spirit of [toolz](https://github.com/pytoolz/toolz), we provide missing features for Python, mainly from the list processing tradition, but with some Haskellisms mixed in. We extend the language with a set of [syntactic macros](https://en.wikipedia.org/wiki/Macro_(computer_science)#Syntactic_macros). We emphasize **clear, pythonic syntax**, and **making features work together**.

The features are built out of, in increasing order of [magic](https://macropy3.readthedocs.io/en/latest/discussion.html#levels-of-magic):

 - Pure Python (e.g. batteries for `itertools`),
 - Macros driving a pure-Python core (e.g. `do`, `let`),
 - Pure macros (e.g. `continuations`, `lazify`, `dbg`).

This depends on the purpose of each feature, as well as ease-of-use considerations. See our [design notes](doc/design-notes.md) for more information.

### Dependencies

None required.  
[MacroPy](https://github.com/azazel75/macropy) optional, to enable the syntactic macro layer.

### Documentation

[Pure-Python feature set](doc/features.md)  
[Syntactic macro feature set](macro_extras/README.md)  
[Design notes](doc/design-notes.md): for more insight into the design choices of ``unpythonic``.

## Installation

**PyPI**

``pip3 install unpythonic --user``

or

``sudo pip3 install unpythonic``

**GitHub**

Clone (or pull) from GitHub. Then,

``python3 setup.py install --user``

or

``sudo python3 setup.py install``

**Uninstall**

Uninstallation must be invoked in a folder which has no subfolder called ``unpythonic``, so that ``pip`` recognizes it as a package name (instead of a filename). Then,

``pip3 uninstall unpythonic``

or

``sudo pip3 uninstall unpythonic``

## License

All original code is released under the 2-clause [BSD license](LICENSE.md).

For sources and licenses of fragments originally seen on the internet, see [AUTHORS](AUTHORS.md).


## Acknowledgements

Thanks to [TUT](http://www.tut.fi/en/home) for letting me teach [RAK-19006 in spring term 2018](https://github.com/Technologicat/python-3-scicomp-intro); early versions of parts of this library were originally developed as teaching examples for that course. Thanks to @AgenttiX for feedback.

The trampoline implementation of ``unpythonic.tco`` takes its remarkably clean and simple approach from ``recur.tco`` in [fn.py](https://github.com/fnpy/fn.py). Our main improvements are a cleaner syntax for the client code, and the addition of the FP looping constructs.

Another important source of inspiration was [tco](https://github.com/baruchel/tco) by Thomas Baruchel, for thinking about the possibilities of TCO in Python.

## Python-related FP resources

Python clearly wants to be an impure-FP language. A decorator with arguments *is a curried closure* - how much more FP can you get?

- [Awesome Functional Python](https://github.com/sfermigier/awesome-functional-python), especially a list of useful libraries. Some picks:

  - [fn.py: Missing functional features of fp in Python](https://github.com/fnpy/fn.py) (actively maintained fork). Includes e.g. tail call elimination by trampolining, and a very compact way to recursively define infinite streams.

  - [more-itertools: More routines for operating on iterables, beyond itertools.](https://github.com/erikrose/more-itertools)

  - [boltons: Like builtins, but boltons.](https://github.com/mahmoud/boltons) Includes yet more itertools, and much more.

  - [toolz: A functional standard library for Python](https://github.com/pytoolz/toolz)

  - [funcy: A fancy and practical functional tools](https://github.com/suor/funcy/)

  - [pyrsistent: Persistent/Immutable/Functional data structures for Python](https://github.com/tobgu/pyrsistent)

  - [pampy: Pattern matching for Python](https://github.com/santinic/pampy) (pure Python, no AST transforms!)

- [List of languages that compile to Python](https://github.com/vindarel/languages-that-compile-to-python) including Hy, a Lisp (in the [Lisp-2](https://en.wikipedia.org/wiki/Lisp-1_vs._Lisp-2) family) that can use Python libraries.

Old, but interesting:

- [Peter Norvig (2000): Python for Lisp Programmers](http://www.norvig.com/python-lisp.html)

- [David Mertz (2001): Charming Python - Functional programming in Python, part 2](https://www.ibm.com/developerworks/library/l-prog2/index.html)
