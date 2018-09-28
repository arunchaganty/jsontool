"""
Simple JSON expressions
"""
import re
import pdb
import os

import numpy as np

from lark import Lark, UnexpectedInput
from lark import Transformer as _Transformer
from jsonpath_ng import parse as parse_jsonpath

def _print(x):
    print(x)
    return x

# Lookup table of possible functions.
_FUNCTIONS = {
    "mean": lambda vs: np.mean(vs) if vs else None,
    "sum": lambda vs: np.sum(vs) if vs else None,
    "max": lambda vs: np.max(vs) if vs else None,
    "median": lambda vs: np.median(vs) if vs else None,
    "len": len,
    "not": lambda v: not v,
    "tern": lambda v: 1 if (v or 0) > 0 else (0 if (v or 0) < 0 else None),
    "scale": lambda vs, r: [v / r for v in vs],
    "agreement": lambda xs, ys: np.mean([1 if x == y else 0 for x, y in zip(xs,ys)]),
    "cnst": lambda v, l: [v for _ in range(l)],
    "match": lambda v, v_: re.match(v, v_) != None,
    "find": lambda v, v_: len(re.findall(v, v_)) > 0,
    "imatch": lambda v, v_: re.match(v, v_, flags=re.IGNORECASE) != None,
    "ifind": lambda v, v_: len(re.findall(v, v_, flags=re.IGNORECASE)) > 0,
}

def _fn(v):
    return lambda _: v
def _condense(items):
    if items:
        return items[0] if len(items) == 1 else items
    else:
        return None
def _skip_nones(vs):
    ret = [v for v in vs if v is not None]
    return ret if ret else None

class Transformer(_Transformer):
    def jsonpath(self, items):
        path = parse_jsonpath(items[0])
        return lambda obj: _condense([match.value for match in path.find(obj)])

    boolean = lambda self, items: _fn(items[0] == "True")
    number = lambda self, items: _fn(float(items[0]))
    string = lambda self, items: _fn(items[0][1:-1]) # Remove surrounding quotes
    literal = lambda self, items: _FUNCTIONS[items[0]]

    comparison_op = lambda self, items: items[0]
    boolean_op = lambda self, items: items[0]
    arith_op = lambda self, items: items[0]
    eq_op = lambda self, items: items[0]
    literal = lambda self, items: items[0]

    def map_expr(self, items):
        fn, *args = items
        fn = _FUNCTIONS[fn]

        def _ret(obj):
            vs = [arg(obj) for arg in args]
            # Each of these is a list
            assert all(isinstance(v, list) for v in vs)

            ret = [fn(*vs_) for vs_ in zip(*vs)]
            ret = _skip_nones(ret)

            return ret
        return _ret

    def reduce_expr(self, items):
        fn, *args = items
        fn = _FUNCTIONS[fn]
        return lambda obj: fn(*[arg(obj) for arg in args])

    def arith_expr(self, items):
        assert len(items) == 3
        l, op, r = items
        if op == "+":
            return lambda obj: l(obj) + r(obj)
        if op == "-":
            return lambda obj: l(obj) - r(obj)
        if op == "*":
            return lambda obj: l(obj) * r(obj)
        if op == "/":
            return lambda obj: l(obj) / r(obj)

    def boolean_atom(self, items):
        assert len(items) == 3
        l, op, r = items

        if op == "==":
            return lambda obj: l(obj) == r(obj)
        if op == "!=":
            return lambda obj: l(obj) != r(obj)
        if op == "<=":
            return lambda obj: l(obj) <= r(obj)
        if op == "<":
            return lambda obj: l(obj) < r(obj)
        if op == ">":
            return lambda obj: l(obj) > r(obj)
        if op == ">=":
            return lambda obj: l(obj) >= r(obj)

    def boolean_expr(self, items):
        assert len(items) == 3
        l, op, r = items
        if op == "&&":
            return lambda obj: l(obj) and r(obj)
        if op == "||":
            return lambda obj: l(obj) or r(obj)

    def conditional_expr(self, items):
        assert len(items) == 2 or len(items) == 3
        if len(items) == 2:
            cond, l = items
            return lambda obj: l(obj) if cond(obj) else None
        if len(items) == 3:
            cond, l, r = items
            return lambda obj: l(obj) if cond(obj) else r(obj)

GRAMMAR_PATH = os.path.join(os.path.dirname(__file__), "grammar.lark")
with open(GRAMMAR_PATH) as f:
    _GRAMMAR = f.read()
    _PARSER = Lark(_GRAMMAR, start="expr")
_TRANSFORMER = Transformer()

def parse_expr(expr):
    try:
        tree = _PARSER.parse(expr)
        return _TRANSFORMER.transform(tree)
    except UnexpectedInput:
        raise ValueError("Could not parse {}".format(expr))

def test_parse_expr():
    obj = {
        "apples": 1,
        "bananas": {
            "apples": 2,
            "bananas": {
                "apples": 3,
                }
            },
        "oranges": True,
        "tomatoes": False,
        "carrots": [1,2,3,4],
        "cantaloupes": 0,
        "watermelons": -1,
        "turnip": [1,1,0,-1],
        "melon": "this is a test",
        }

    assert parse_expr("$.apples")(obj) == 1
    assert parse_expr("$.bananas.apples")(obj) == 2
    assert parse_expr("$.bananas.bananas.apples")(obj) == 3

    assert parse_expr("$.apples < 3")(obj) is True
    assert parse_expr("$.apples <= 1")(obj) is True
    assert parse_expr("$.apples + $.bananas.apples")(obj) == 1 + 2

    assert parse_expr("$.oranges")(obj) is True
    assert parse_expr("$.oranges => 1")(obj) == 1
    assert parse_expr("$.tomatoes => 1")(obj) is None
    assert parse_expr("$.oranges ? 1 : 2")(obj) == 1
    assert parse_expr("$.tomatoes ? 1 : 2")(obj) == 2

    assert parse_expr("sum($.carrots)")(obj) == 10
    assert parse_expr("mean($.carrots)")(obj) == 2.5
    assert parse_expr("max($.carrots)")(obj) == 4

    assert parse_expr("tern($.apples)")(obj) == 1
    assert parse_expr("tern($.cantaloupes)")(obj) is None
    assert parse_expr("tern($.watermelons)")(obj) == 0
    assert parse_expr("mean(tern{$.turnip})")(obj) == 2/3

    assert parse_expr('match("this", $.melon)')(obj) == True
    assert parse_expr('match("test", $.melon)')(obj) == False
    assert parse_expr('find("this", $.melon)')(obj) == True
    assert parse_expr('find("test", $.melon)')(obj) == True
    assert parse_expr('find("tast", $.melon)')(obj) == False
