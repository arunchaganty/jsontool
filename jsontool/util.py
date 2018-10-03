"""
Utilities
"""

import re
import csv
import json
import logging

logger = logging.getLogger(__name__)

def JsonFile(*args, **kwargs):
    def _ret(fname):
        return json.load(open(fname, *args, **kwargs))
    return _ret

class JsonWriter():
    def __init__(self, stream, indent=None):
        self.stream = stream
        self.indent = indent

    def write(self, obj):
        self.stream.write(json.dumps(obj, indent=self.indent))
        self.stream.write("\n")


def load_jsonl(fstream):
    if isinstance(fstream, str):
        with open(fstream) as fstream_:
            return list(load_jsonl(fstream_))

    return (json.loads(line) for line in fstream)

def save_jsonl(fstream, objs):
    if isinstance(fstream, str):
        with open(fstream, "w") as fstream_:
            save_jsonl(fstream_, objs)
        return

    for obj in objs:
        fstream.write(json.dumps(obj, sort_keys=True))
        fstream.write("\n")

def first(itable):
    return next(iter(itable))

def force_user_input(prompt, options):
    ret = None
    while ret is None:
        ret = input(prompt + str(options) + ": ").strip()
        if ret.lower() not in options:
            ret = None
    return ret

def obj_diff(obj, obj_):
    ret = True
    for k in obj:
        if k not in obj_:
            print("Key {} missing in arg2".format(k))
            ret = False
        if obj[k] != obj_[k]:
            if isinstance(obj[k], dict) and isinstance(obj_[k], dict):
                obj_diff(obj[k], obj_[k])
                ret = False
            else:
                print("{}: args1 has {}, args2 has {}".format(k, obj[k], obj_[k]))
    for k in obj_:
        if k not in obj:
            print("Key {} missing in arg1".format(k))
            ret = False
    return ret


class Visitor():
    def visit_dict(self, obj, path):
        assert isinstance(obj, dict)

        for key, value in obj.items():
            path.append(key)
            self.visit(value, path)
            path.pop()

    def visit_list(self, obj, path):
        assert isinstance(obj, list)
        for i, obj_ in enumerate(obj):
            path.append(i)
            self.visit(obj_, i)
            path.pop()

    def visit_value(self, obj, path):
        pass

    def visit(self, obj, path=None):
        if path is None:
            path = []
        if isinstance(obj, dict):
            self.visit_dict(obj, path)
        elif isinstance(obj, list):
            self.visit_list(obj, path)
        else:
            self.visit_value(obj, path)

def visit_obj(fn, obj, path=None):
    """
    Super simplified visitor: no special case for lists.
    """
    if path is None: path = []
    for key, value in sorted(obj.items()):
        path.append(key)
        if isinstance(value, dict):
            visit_obj(fn, value, path)
        else:
            fn(value, path)
        path.pop()

def list_schema(obj):
    ret = []

    _to_key = lambda k: re.sub(r"[^a-zA-Z]", "", k)
    def _get_schema(value, path):
        ret.append(".".join(map(_to_key, path)))

    visit_obj(_get_schema, obj)
    return ret

def list_obj(obj):
    ret = []

    def _to_str(value, _):
        if isinstance(value, list):
            ret.append(",".join(map(str, value)))
        else:
            ret.append(str(value))

    visit_obj(_to_str, obj)
    return ret

def load_csv(fstream, delimiter="\t"):
    reader = csv.reader(fstream, delimiter=delimiter)

    header = next(reader)
    header = [re.sub("[^a-zA-Z0-9]", "", h) for h in header]
    for row in reader:
        obj = {key: value for key, value in zip(header, row)}
        yield obj
