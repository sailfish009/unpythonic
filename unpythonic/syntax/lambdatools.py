# -*- coding: utf-8 -*-
"""Lambdas with multiple expressions, local variables, and a name."""

from ast import (Lambda, List, Name, Assign, Subscript, Call,
                 FunctionDef, Attribute, keyword, Dict, Str, arg,
                 copy_location)
from .astcompat import AsyncFunctionDef
from copy import deepcopy

from macropy.core.quotes import macros, q, u, ast_literal, name
from macropy.core.hquotes import macros, hq  # noqa: F811, F401
from macropy.core.walkers import Walker
from macropy.quick_lambda import f, _  # _ for re-export only  # noqa: F401

from ..dynassign import dyn
from ..misc import namelambda
from ..fun import orf
from ..env import env

from .letdo import do
from .letdoutil import islet, isenvassign, UnexpandedLetView, UnexpandedEnvAssignView, ExpandedDoView
from .util import (is_decorated_lambda, isx, make_isxpred, has_deco,
                   destructure_decorated_lambda, detect_lambda, splice)

def multilambda(block_body):
    @Walker
    def transform(tree, *, stop, **kw):
        if type(tree) is not Lambda or type(tree.body) is not List:
            return tree
        bodys = tree.body
        # bracket magic:
        # - stop() to prevent recursing to the implicit lambdas generated
        #   by the "do" we are inserting here
        #   - for each item, "do" internally inserts a lambda to delay execution,
        #     as well as to bind the environment
        #   - we must do() instead of hq[do[...]] for pickling reasons
        # - but recurse manually into each *do item*; these are explicit
        #   user-provided code so we should transform them
        stop()
        bodys = transform.recurse(bodys)
        tree.body = do(bodys)  # insert the do, with the implicit lambdas
        return tree
    # multilambda should expand first before any let[], do[] et al. that happen
    # to be inside the block, to avoid misinterpreting implicit lambdas
    # generated by those constructs.
    yield transform.recurse(block_body)

def namedlambda(block_body):
    def issingleassign(tree):
        return type(tree) is Assign and len(tree.targets) == 1 and type(tree.targets[0]) is Name

    # detect a manual curry
    iscurry = make_isxpred("curry")
    def iscurrywithfinallambda(tree):
        if not (type(tree) is Call and isx(tree.func, iscurry) and tree.args):
            return False
        return type(tree.args[-1]) is Lambda

    # Detect an autocurry from an already expanded "with curry".
    # CAUTION: These must match what unpythonic.syntax.curry.curry uses in its output.
    iscurrycall = make_isxpred("currycall")
    iscurryf = orf(make_isxpred("curryf"), make_isxpred("curry"))  # auto or manual curry in a "with curry"
    def isautocurrywithfinallambda(tree):
        if not (type(tree) is Call and isx(tree.func, iscurrycall) and tree.args and
                type(tree.args[-1]) is Call and isx(tree.args[-1].func, iscurryf)):
            return False
        return type(tree.args[-1].args[-1]) is Lambda

    def iscallwithnamedargs(tree):
        return type(tree) is Call and tree.keywords

    # If `tree` is a (bare or decorated) lambda, inject run-time code to name
    # it as `myname` (str); else return `tree` as-is.
    def nameit(myname, tree):
        match, thelambda = False, None
        # for decorated lambdas, match any chain of one-argument calls.
        d = is_decorated_lambda(tree, mode="any") and not has_deco(tree, "namelambda")
        c = iscurrywithfinallambda(tree)
        # this matches only during the second pass (after "with curry" has expanded)
        # so it can't have namelambda already applied
        if isautocurrywithfinallambda(tree):  # "currycall(..., curryf(lambda ...: ...))"
            match = True
            thelambda = tree.args[-1].args[-1]
            tree.args[-1].args[-1] = hq[namelambda(u[myname])(ast_literal[thelambda])]
        elif type(tree) is Lambda or d or c:
            match = True
            if d:
                decorator_list, thelambda = destructure_decorated_lambda(tree)
            elif c:
                thelambda = tree.args[-1]
            else:
                thelambda = tree
            tree = hq[namelambda(u[myname])(ast_literal[tree])]  # plonk it as outermost and hope for the best
        return tree, thelambda, match

    @Walker
    def transform(tree, *, stop, **kw):
        if islet(tree, expanded=False):  # let bindings
            stop()
            view = UnexpandedLetView(tree)
            for b in view.bindings:
                b.elts[1], thelambda, match = nameit(b.elts[0].id, b.elts[1])
                if match:
                    thelambda.body = rec(thelambda.body)
                else:
                    b.elts[1] = rec(b.elts[1])
            view.body = rec(view.body)
        # assumption: no one left-shifts by a literal lambda :)
        elif isenvassign(tree):  # f << (lambda ...: ...)
            stop()
            view = UnexpandedEnvAssignView(tree)
            view.value, thelambda, match = nameit(view.name, view.value)
            if match:
                thelambda.body = rec(thelambda.body)
            else:
                view.value = rec(view.value)
        elif issingleassign(tree):  # f = lambda ...: ...
            stop()
            tree.value, thelambda, match = nameit(tree.targets[0].id, tree.value)
            if match:
                thelambda.body = rec(thelambda.body)
            else:
                tree.value = rec(tree.value)
        elif iscallwithnamedargs(tree):  # foo(f=lambda: ...)
            stop()
            for kw in tree.keywords:
                if kw.arg is None:  # **kwargs in Python 3.5+
                    kw.value = rec(kw.value)
                    continue
                # a single named arg
                kw.value, thelambda, match = nameit(kw.arg, kw.value)
                if match:
                    thelambda.body = rec(thelambda.body)
                else:
                    kw.value = rec(kw.value)
            tree.args = rec(tree.args)
            if hasattr(tree, "starargs"):  # Python 3.4
                tree.starargs = rec(tree.starargs)  # pragma: no cover
            if hasattr(tree, "kwargs"):  # Python 3.4
                tree.kwargs = rec(tree.kwargs)  # pragma: no cover
        elif type(tree) is Dict:  # {"f": lambda: ..., "g": lambda: ...}
            stop()
            lst = list(zip(tree.keys, tree.values))
            for j in range(len(lst)):
                k, v = tree.keys[j], tree.values[j]
                if k is None:  # {..., **d, ...}
                    tree.values[j] = rec(v)
                else:
                    if type(k) is Str:  # TODO: Python 3.8 ast.Constant
                        tree.values[j], thelambda, match = nameit(k.s, v)
                        if match:
                            thelambda.body = rec(thelambda.body)
                        else:
                            tree.values[j] = rec(v)
                    else:
                        tree.keys[j] = rec(k)
                        tree.values[j] = rec(v)
        return tree

    rec = transform.recurse
    newbody = yield [rec(stmt) for stmt in block_body]   # first pass: transform in unexpanded let[] forms
    return [rec(stmt) for stmt in newbody]               # second pass: transform in expanded autocurry

def quicklambda(block_body):
    # TODO/FIXME: `f_transform` is actually `f` from `macropy.quick_lambda`,
    # TODO/FIXME: stripped into a bare syntax transformer.
    #
    # We have copied the implementation here, because the released MacroPy3 1.1.0b2
    # does not autogenerate a `.transform` attribute for macros; in the HEAD version,
    # that attribute allows accessing the underlying syntax transformer.
    #
    # Used under the MIT license.
    # Copyright (c) 2013-2018, Li Haoyi, Justin Holmgren, Alberto Berti and all the other contributors.
    gen_sym = dyn.gen_sym
    def f_transform(tree):  # pragma: no cover, fallback for MacroPy 1.1.0b2
        @Walker
        def underscore_search(tree, collect, **kw):
            if isinstance(tree, Name) and tree.id == "_":
                name = gen_sym("_")
                tree.id = name
                collect(name)
                return tree
        tree, used_names = underscore_search.recurse_collect(tree)
        new_tree = q[lambda: ast_literal[tree]]
        new_tree.args.args = [arg(arg=x) for x in used_names]
        return new_tree

    # The rest is our code.
    def isquicklambda(tree):
        return type(tree) is Subscript and type(tree.value) is Name and tree.value.id == "f"
    @Walker
    def transform(tree, **kw):
        if isquicklambda(tree):
            # TODO: With MacroPy3 from azazel75/macropy/HEAD, we can call `f.transform`
            # TODO: and we don't need our own `f_transform` function. Kill the hack
            # TODO: once a new version of MacroPy3 is released.
            if hasattr(f, "transform"):
                return f.transform(tree.slice.value)
            return f_transform(tree.slice.value)  # pragma: no cover, fallback for MacroPy3 1.1.0b2
        return tree
    new_block_body = [transform.recurse(stmt) for stmt in block_body]
    yield new_block_body

def envify(block_body):
    # first pass, outside-in
    userlambdas = detect_lambda.collect(block_body)
    yield block_body

    # second pass, inside-out
    def getargs(tree):  # tree: FunctionDef, AsyncFunctionDef, Lambda
        a = tree.args
        argnames = [x.arg for x in a.args + a.kwonlyargs]
        if a.vararg:
            argnames.append(a.vararg.arg)
        if a.kwarg:
            argnames.append(a.kwarg.arg)
        return argnames

    def isfunctionoruserlambda(tree):
        return ((type(tree) in (FunctionDef, AsyncFunctionDef)) or
                (type(tree) is Lambda and id(tree) in userlambdas))

    # Create a renamed reference to the env() constructor to be sure the Call
    # nodes added by us have a unique .func (not used by other macros or user code)
    _ismakeenv = make_isxpred("_envify")
    _envify = env

    gen_sym = dyn.gen_sym
    @Walker
    def transform(tree, *, bindings, enames, stop, set_ctx, **kw):
        def isourupdate(thecall):
            if type(thecall.func) is not Attribute:
                return False
            return thecall.func.attr == "update" and any(isx(thecall.func.value, x) for x in enames)

        if isfunctionoruserlambda(tree):
            argnames = getargs(tree)
            if argnames:
                # prepend env init to function body, update bindings
                kws = [keyword(arg=k, value=q[name[k]]) for k in argnames]  # "x" --> x
                newbindings = bindings.copy()
                if type(tree) in (FunctionDef, AsyncFunctionDef):
                    ename = gen_sym("e")
                    theenv = hq[_envify()]
                    theenv.keywords = kws
                    assignment = Assign(targets=[q[name[ename]]],
                                        value=theenv)
                    assignment = copy_location(assignment, tree)
                    tree.body.insert(0, assignment)
                elif type(tree) is Lambda and id(tree) in userlambdas:
                    # We must in general inject a new do[] even if one is already there,
                    # due to scoping rules. If the user code writes to the same names in
                    # its do[] env, this shadows the formals; if it then pops one of its names,
                    # the name should revert to mean the formal parameter.
                    #
                    # inject a do[] and reuse its env
                    tree.body = do(List(elts=[q[name["_here_"]],
                                              tree.body]))
                    view = ExpandedDoView(tree.body)  # view.body: [(lambda e14: ...), ...]
                    ename = view.body[0].args.args[0].arg  # do[] environment name
                    theupdate = Attribute(value=q[name[ename]], attr="update")
                    thecall = q[ast_literal[theupdate]()]
                    thecall.keywords = kws
                    tree.body = splice(tree.body, thecall, "_here_")
                newbindings.update({k: Attribute(value=q[name[ename]], attr=k) for k in argnames})  # "x" --> e.x
                set_ctx(enames=enames + [ename])
                set_ctx(bindings=newbindings)
        else:
            # leave alone the _envify() added by us
            if type(tree) is Call and (isx(tree.func, _ismakeenv) or isourupdate(tree)):
                stop()
            # transform env-assignments into our envs
            elif isenvassign(tree):
                view = UnexpandedEnvAssignView(tree)
                if view.name in bindings.keys():
                    envset = Attribute(value=bindings[view.name].value, attr="set")
                    return q[ast_literal[envset](u[view.name], ast_literal[view.value])]
            # transform references to currently active bindings
            elif type(tree) is Name and tree.id in bindings.keys():
                # We must be careful to preserve the Load/Store/Del context of the name.
                # The default lets MacroPy fix it later.
                ctx = tree.ctx if hasattr(tree, "ctx") else None
                out = deepcopy(bindings[tree.id])
                out.ctx = ctx
                return out
        return tree
    return transform.recurse(block_body, bindings={}, enames=[])
