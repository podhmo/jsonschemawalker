# -*- coding:utf-8 -*-
import pytest
from datetime import datetime
import pytz


def _callFUT(*args, **kwargs):
    from jsonschemawalker import to_python
    return to_python(*args, **kwargs)


def test_atom__no_convert():
    schema = {"type": "string"}
    result = _callFUT(schema, "foo")
    assert result == "foo"


cands = [
    ("integer", None, None),
    ("integer", "10", 10),
    ("number", "1.0", 1.0),
    ("boolean", "true", True),
    ("boolean", "false", False),
    ("null", "null", None),
]


@pytest.mark.parametrize("type, value, expected", cands)
def test_atom_convert(type, value, expected):
    schema = {"type": type}
    result = _callFUT(schema, value)
    assert result == expected


cands = [
    ("string", "date-time", None, None),
    ("string", "date-time", "2000-01-01T00:00:00Z", datetime(2000, 1, 1, 0, 0, 0, 0, pytz.utc)),
]


@pytest.mark.parametrize("type, format, value, expected", cands)
def test_atom_convert__with_format(type, format, value, expected):
    schema = {"type": type, "format": format}
    result = _callFUT(schema, value)
    assert result == expected


# todo: anyof, subschema
def test_object():
    schema = {"type": "object",
              "properties": {"name": {"type": "string"}, "age": {"type": "integer"}}}
    value = {"name": "foo", "age": "20"}
    result = _callFUT(schema, value)
    assert result == {"name": "foo", "age": 20}


def test_object__slackoff():
    schema = {"type": "object",
              "properties": {"name": {}, "age": {}}}
    value = {"name": "foo", "age": "20"}
    result = _callFUT(schema, value)
    assert result == {"name": "foo", "age": "20"}


def test_object__no_type():
    schema = {"properties": {"name": {"type": "string"}, "age": {"type": "integer"}}}
    value = {"name": "foo", "age": "20"}
    result = _callFUT(schema, value)
    assert result == {"name": "foo", "age": 20}


def test_object__subschema():
    schema = {"type": "object",
              "properties": {"group": {"properties": {"name": {"type": "string"}}},
                             "name": {"type": "string"}}}
    value = {"group": {"name": "Blue"}, "name": "foo"}
    result = _callFUT(schema, value)
    assert result == {"name": "foo", "group": {"name": "Blue"}}


def test_object__with_ref__object():
    schema = {"type": "object",
              "definitions": {
                  "Group": {"properties": {"name": {"type": "string"}}}
              },
              "properties": {"group": {"$ref": "#/definitions/Group"},
                             "name": {"type": "string"}}}
    value = {"group": {"name": "Blue"}, "name": "foo"}
    result = _callFUT(schema, value)
    assert result == {"name": "foo", "group": {"name": "Blue"}}


def test_object__with_oneOf__Success():
    schema = {"type": "object",
              "definitions": {
                  "Success": {"properties": {"value": {}}},
                  "Failure": {"properties": {"name": {"type": "string"}, "message": {"type": "string"}}}
              },
              "oneOf": [{"$ref": "#/definitions/Success"}, {"$ref": "#/definitions/Failure"}]
              }
    value = {"value": {"data": {"result": "hai"}, "status": "ok"}}
    result = _callFUT(schema, value)
    assert result == {'value': {'data': {'result': 'hai'}, 'status': 'ok'}}


def test_object__with_oneOf__Failure():
    schema = {"type": "object",
              "definitions": {
                  "Success": {"properties": {"value": {}}},
                  "Failure": {"properties": {"name": {"type": "string"}, "message": {"type": "string"}}}
              },
              "oneOf": [{"$ref": "#/definitions/Success"}, {"$ref": "#/definitions/Failure"}]
              }
    value = {"name": "runtime-error", "message": "anything is wrong!"}
    result = _callFUT(schema, value)
    assert result == {"name": "runtime-error", "message": "anything is wrong!"}


def test_object__any_of_Point2():
    schema = {"type": "object",
              "definitions": {
                  "Point2": {"properties": {"x": {"type": "integer"}, "y": {"type": "integer"}}},
                  "Point3": {"properties": {"x": {"type": "integer"}, "y": {"type": "integer"}, "z": {"type": "integer"}}}
              },
              "anyOf": [{"$ref": "#/definitions/Point2"}, {"$ref": "#/definitions/Point3"}]
              }
    value = {"x": "10", "y": "20"}
    result = _callFUT(schema, value)
    assert result == {"x": 10, "y": 20}


def test_object__any_of_Point3():
    schema = {"type": "object",
              "definitions": {
                  "Point2": {"properties": {"x": {"type": "integer"}, "y": {"type": "integer"}}},
                  "Point3": {"properties": {"x": {"type": "integer"}, "y": {"type": "integer"}, "z": {"type": "integer"}}}
              },
              "anyOf": [{"$ref": "#/definitions/Point2"}, {"$ref": "#/definitions/Point3"}]
              }
    value = {"x": "10", "y": "20", "z": "30"}
    result = _callFUT(schema, value)
    assert result == {"x": 10, "y": 20, "z": 30}


def test_object__all_of():
    schema = {"type": "object",
              "definitions": {
                  "HasName": {"properties": {"name": {"type": "string"}}, "required": ["name"]},
                  "HasCreatedAt": {"properties": {"created_at": {"type": "string", "format": "date-time"}}}
              },
              "allOf": [{"$ref": "#/definitions/HasName"}, {"$ref": "#/definitions/HasCreatedAt"}]
              }
    value = {"name": "foo", "created_at": "2000-01-01T01:01:00Z"}
    result = _callFUT(schema, value)
    assert result == {"name": "foo", "created_at": datetime(2000, 1, 1, 1, 1, 0, 0, pytz.utc)}


def test_object_pattern_properties():
    schema = {
        "type": "object",
        "patternProperties": {
            "^test_[a-zA-Z0-9_]+$": {"type": "string"}
        },
        "additionalProperties": False
    }
    value = {
        "test_foo": "ok",
        "test_bar": "ok",
        "test_boo": "ok"
    }
    result = _callFUT(schema, value)
    assert result == {'test_bar': 'ok', 'test_boo': 'ok', 'test_foo': 'ok'}


def test_object_pattern_properties__additional_properties():
    schema = {
        "type": "object",
        "patternProperties": {
            "^test_[a-zA-Z0-9_]+$": {"type": "string"}
        },
        "additionalProperties": True
    }
    value = {
        "test_foo": "ok",
        "test_bar": "ok",
        "test_boo": "ok",
        "foo": "foo"
    }
    result = _callFUT(schema, value)
    assert result == {'test_bar': 'ok', 'test_boo': 'ok', 'test_foo': 'ok', "foo": "foo"}


def test_object__with_ref__array():
    schema = {"type": "object",
              "definitions": {
                  "User": {"properties": {"name": {"type": "string"}, "age": {"type": "integer"}}}
              },
              "properties": {"users": {"type": "array", "items": {"$ref": "#/definitions/User"}}}}
    value = {"users": [{"name": "foo", "age": "20"}]}
    result = _callFUT(schema, value)
    assert result == {"users": [{"name": "foo", "age": 20}]}
