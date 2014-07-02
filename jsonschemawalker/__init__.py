# -*- coding:utf-8 -*-
import logging
import re
from dateutil import parser as du_parser
logger = logging.getLogger(__name__)


def identity(v):
    return v


def as_none(v):
    return None


def as_bool(s):
    b = s.lower()
    return not (b == "false")


def as_datetime(s):
    return du_parser.parse(s)

# type, format -> convert-function
default_mapping = {
    ("string", None): identity,
    ("string", "date-time"): as_datetime,
    ("integer", None): int,
    ("number", None): float,
    ("boolean", None): as_bool,
    ("null", None): as_none
}


class Converter(object):
    def __init__(self, mapping, default=None, kindly=True):
        self.mapping = mapping
        self.default = default
        self.kindly = kindly

    def get_convert(self, schema):
        k = (schema.get("type"), schema.get("format"))
        v = self.mapping.get(k)
        if v is None and self.kindly:
            k = self.mapping.get(schema.get("type"), None)
            v = self.mapping.get(k, identity)
        return v

    def __call__(self, schema, value):
        if value is None:
            return self.default
        return self.get_convert(schema)(value)


class Control(object):
    def __init__(self):
        self.merged_cache = {}
        self.regexp_cache = {}

    def get_wrapper(self, schema, params, dict_of_wrapper):
        if "title" in schema:
            wrapper = dict_of_wrapper.get(schema["title"])
        elif "$ref" in schema:
            path = schema["$ref"]
            name = path.replace("#/definitions/", "")
            wrapper = dict_of_wrapper.get(name)
        else:
            wrapper = None

        if wrapper is None:
            return params
        else:
            return wrapper(**params)

    def get_regexp(self, s):
        try:
            return self.regexp_cache[s]
        except KeyError:
            v = self.regexp_cache[s] = re.compile(s)
            return v

    def iterate_properties(self, schema, value):
        if "patternProperties" in schema:
            additional_properties = schema.get("additionalProperties", True)
            cands = [(self.get_regexp(s), v) for s, v in schema["patternProperties"].items()]
            for k in value:
                used = not additional_properties
                for regexp, v in cands:
                    m = regexp.search(k)
                    if m is not None:
                        yield k, v
                        used = True
                        break
                if not used:
                    yield k, {}
        else:
            if "properties" not in schema:
                for k, v in schema.items():
                    yield k, v
            properties = schema["properties"]
            if hasattr(properties, "$order"):
                for k in properties["$order"]:
                    yield k, properties[k]
            else:
                for k, v in properties.items():
                    yield k, v

    def track_reference(self, schema, root_schema):
        ref = schema["$ref"]
        if not ref.startswith("#/"):
            raise NotImplemented(ref)
        target = root_schema
        for k in ref.split("/")[1:]:
            target = target[k]
        return target

    def detect_property_names(self, schema):
        # todo: patternProperties
        if "properties" in schema:
            return schema["properties"].keys()
        else:
            return schema.keys()

    def detect_matched(self, candidates, value, root_schema):
        xs = []
        for c in candidates:
            if "$ref" in c:
                exact_c = self.track_reference(c, root_schema)
            else:
                exact_c = c
            names = self.detect_property_names(exact_c)
            score = sum((1 if name in value else 0) for name in names)
            if len(names) == len(value):
                score += 1
            xs.append((score, c))
        return max(xs, key=lambda p: p[0])[1]

    def detect_merged(self, candidates, root_schema):
        k = tuple([d["$ref"] for d in candidates])
        try:
            return self.merged_cache[k]
        except KeyError:
            new_schema = {"type": "object", "properties": {}}
            properties = new_schema["properties"]
            for c in candidates:
                properties.update(self.track_reference(c, root_schema)["properties"])
            self.merged_cache[k] = new_schema
            return new_schema


class Walker(object):
    def __init__(self, schema,
                 wrappers=None,
                 factory=dict,
                 control=Control(),
                 converter=Converter(default_mapping)):
        self.wrappers = wrappers or {}
        self.converter = converter
        self.control = control
        self.schema = schema
        self.factory = factory

    def __call__(self, value):
        return self.walk(self.schema, value)

    def walk(self, schema, value):
        if schema == {}:
            return value
        type_ = schema.get("type", "object")
        if type_ == "object":
            return self.walk_object(schema, value)
        elif type_ == "array":
            return self.walk_array(schema, value)
        else:
            return self.walk_atom(schema, value)

    def walk_atom(self, schema, value):
        return self.converter(schema, value)

    def walk_reference(self, schema):
        return self.control.track_reference(schema, self.schema)

    def walk_one_of(self, schema, value):
        matched = self.control.detect_matched(schema["oneOf"], value, self.schema)
        return self.walk_object(matched, value)

    def walk_any_of(self, schema, value):
        matched = self.control.detect_matched(schema["anyOf"], value, self.schema)
        return self.walk_object(matched, value)

    def walk_all_of(self, schema, value):
        merged = self.control.detect_merged(schema["allOf"], self.schema)
        return self.walk_object(merged, value)

    def walk_object(self, schema, value):
        if "oneOf" in schema:
            return self.walk_one_of(schema, value)
        elif "anyOf" in schema:
            return self.walk_any_of(schema, value)
        elif "allOf" in schema:
            return self.walk_all_of(schema, value)
        elif "$ref" in schema:
            exact_schema = self.walk_reference(schema)
        else:
            exact_schema = schema
        r = self.factory()
        for k, subschema in self.control.iterate_properties(exact_schema, value):
            r[k] = self.walk(subschema, value.get(k))
        return self.control.get_wrapper(schema, r, self.wrappers)

    def walk_array(self, schema, value):
        subschema = schema["items"]
        return [self.walk(subschema, v) for v in value]


def to_python(schema, data, wrappers=None):
    return Walker(schema, wrappers)(data)
