# -*- coding:utf-8 -*-
import logging
logger = logging.getLogger(__name__)


def identity(v):
    return v


def as_none(v):
    return None


def as_bool(s):
    b = s.lower()
    return not (b == "false")

# type, format -> convert-function
default_mapping = {
    ("string", None): identity,
    ("integer", None): int,
    ("number", None): float,
    ("boolean", None): as_bool,
    ("null", None): as_none
}


class Converter(object):
    def __init__(self, mapping, kindly=True):
        self.mapping = mapping
        self.kindly = kindly

    def get_convert(self, schema):
        k = (schema.get("type"), schema.get("format"))
        v = self.mapping.get(k)
        if v is None and self.kindly:
            k = self.mapping.get(schema.get("type"), None)
            v = self.mapping.get(k, identity)
        return v

    def __call__(self, schema, value):
        return self.get_convert(schema)(value)


class Walker(object):
    def __init__(self, schema, converter=Converter(default_mapping)):
        self.converter = converter
        self.schema = schema

    def __call__(self, value):
        type_ = self.schema["type"]
        if type_ == "object":
            return self.walk_object(self.schema, value)
        elif type_ == "array":
            return self.walk_array(self.schema, value)
        else:
            return self.walk_atom(self.schema, value)

    def walk_atom(self, schema, value):
        return self.converter(schema, value)


def to_python(schema, data):
    return Walker(schema)(data)
