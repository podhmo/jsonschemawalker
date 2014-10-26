# -*- coding:utf-8 -*-

# jsonschema
schema = {
    "title": "User",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
        "created_at": {"type": "string", "format": "date-time"}
    }
}

from jsonschemawalker import to_python

########################################
# json -> python object(dict)
########################################

value = {"name": "foo", "age": 20, "created_at": "2000/01/01T01:00:00Z", "xxx": "yyy"}
python_value = to_python(schema, value)

print(python_value)
# {'created_at': datetime.datetime(2000, 1, 1, 1, 0, tzinfo=tzutc()), 'name': 'foo', 'age': 20}


########################################
# json -> python object(individual data type)
########################################

# define individual data type
from collections import namedtuple
User = namedtuple("User", "name age created_at")

user = to_python(schema, value, {"User": User})
print(user)
# User(name='foo', age=20, created_at=datetime.datetime(2000, 1, 1, 1, 0, tzinfo=tzutc()))


########################################
# supporting patternProperty
########################################

schema = {
    "patternProperties": {
        "answer_[0-9]+": {"type": "integer"},
        "question_[0-9]+": {},
    },
    "additionalProperties": False
}

value = {
    "question_1": "what is your favorite color?",
    "answer_1": "2",
    "question_2": "what is your favorite shape?",
    "answer_2": "1",
    "comment": "this is ignored"
}

python_value = to_python(schema, value)
print(python_value)
# {'question_1': 'what is your favorite color?',
#  'question_2': 'what is your favorite shape?',
#  'answer_1': 2,
#  'answer_2': 1}
