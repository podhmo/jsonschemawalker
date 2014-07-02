# -*- coding:utf-8 -*-
import pytest


def _callFUT(*args, **kwargs):
    from jsonschemawalker import to_python
    return to_python(*args, **kwargs)


def test_atom__no_convert():
    schema = {"type": "string"}
    result = _callFUT(schema, "foo")
    assert result == "foo"


cands = [
    ("integer", "10", 10),
    ("number", "1.0", 1.0),
    ("boolean", "true", True),
    ("boolean", "false", False),
    ("null", "null", None)
]


@pytest.mark.parametrize("type, value, expected", cands)
def test_atom_convert(type, value, expected):
    schema = {"type": type}
    result = _callFUT(schema, value)
    assert result == expected
