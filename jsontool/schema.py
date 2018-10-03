#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extract schema
"""

import pdb
from .expr import parse_expr

def compile_schema(obj):
    if isinstance(obj, dict):
        return {key: compile_schema(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [compile_schema(value) for value in obj]
    elif isinstance(obj, str) and obj.startswith('$'):
        value = obj
        return parse_expr(value)
    else:
        return obj

def apply_schema(schema, obj):
    if isinstance(schema, dict):
        return {key: apply_schema(value, obj) for key, value in schema.items()}
    elif isinstance(schema, list):
        return [apply_schema(value, obj) for value in schema]
    elif callable(schema):
        return schema(obj)
    else:
        return schema

def test_schema():
    obj = {
        "a": 1,
        "b": "apples",
        "c": [2, 3],
        "d": {"a": 4},
        "e": [{"a": 5}, {"a": 6}],
        }

    def test(schema, obj):
        return apply_schema(compile_schema(schema), obj)

    assert test("x", obj) == "x"
    assert test(9, obj) == 9
    assert test("$.a", obj) == 1
    assert test("$.b", obj) == "apples"
    assert test("$.c", obj) == [2, 3]
    assert test("$.d", obj) == {"a": 4}
    assert test("$.e", obj) == [{"a": 5}, {"a": 6}]
    assert test("$.e..a", obj) == [5, 6]

    assert test({"a": "$.a"}, obj) == {"a": 1}
    assert test({"a": {"b": "$.e..a"}}, obj) == {"a": {"b": [5,6]}}

    assert test("$.*", obj) == [1, "apples", [2, 3], {"a": 4}, [{"a": 5}, {"a": 6}]]
