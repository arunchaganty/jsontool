#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSONtool
"""
import re
import pdb
import time
import sys
import json
import csv
import logging
from collections import defaultdict
from pprint import pprint

from tqdm import tqdm, trange
from .expr import parse_expr
from .util import load_jsonl, list_schema, list_obj, JsonWriter, load_csv
from .schema import parse_schema, apply_schema

logger = logging.getLogger(__name__)

def do_csv(args):
    writer = csv.writer(args.output, delimiter=args.delimiter)
    data = load_jsonl(args.input)

    datum = next(data)
    header = list_schema(datum)

    writer.writerow(header)
    writer.writerow(list_obj(datum))
   
    for datum in tqdm(data):
        writer.writerow(list_obj(datum))

def do_filter(args):
    writer = JsonWriter(args.output)
    exprs = [parse_expr(e) for e in args.exprs]

    for obj in tqdm(load_jsonl(args.input)):
        try:
            if args.all and all(expr(obj) for expr in exprs):
                writer.write(obj)
            elif any(expr(obj) for expr in exprs):
                writer.write(obj)
        except:
            pass

def do_pp(args):
    writer = JsonWriter(args.output, indent=args.indent)

    for obj in load_jsonl(args.input):
        writer.write(obj)

def do_extract(args):
    schema = parse_schema(json.loads(args.schema))

    writer = JsonWriter(args.output)

    for obj in load_jsonl(args.input):
        obj_ = apply_schema(schema, obj)
        if args.expand_list and isinstance(obj_, list):
            for elem in obj_:
                writer.write(elem)
        else:
            writer.write(obj_)

def do_import(args):
    writer = JsonWriter(args.output)

    if args.format == "csv":
        for obj in load_csv(args.input, "\t"):
            writer.write(obj)


def main():
    logging.basicConfig(level=logging.INFO)

    import argparse
    parser = argparse.ArgumentParser(description='jsontool: swiss army knife for JSONL files')
    parser.set_defaults(func=None)

    subparsers = parser.add_subparsers()
    command_parser = subparsers.add_parser('csv', help='Convert to csv')
    command_parser.add_argument('-o', '--output', type=argparse.FileType('w'), default=sys.stdout, help="Output CSV file")
    command_parser.add_argument('-d', '--delimiter', default='\t', help="Delimiter to use to both parse input and write output.")
    command_parser.add_argument('-i', '--input', type=argparse.FileType('r'), default=sys.stdin, help="Input JSONL file")
    command_parser.set_defaults(func=do_csv)

    command_parser = subparsers.add_parser('filter', help='Filter json objects')
    command_parser.add_argument('-o', '--output', type=argparse.FileType('w'), default=sys.stdout, help="Output JSONL file")
    command_parser.add_argument('-e', '--exprs', type=str, nargs="+", required=True, help="Filter expressions.")
    command_parser.add_argument('-a', '--all', action="store_true", help="Do all expressions have to match?")
    command_parser.add_argument('-i', '--input', type=argparse.FileType('r'), default=sys.stdin, help="Input JSONL file")
    command_parser.set_defaults(func=do_filter)

    command_parser = subparsers.add_parser('import', help='Import from another file format')
    command_parser.add_argument('-o', '--output', type=argparse.FileType('w'), default=sys.stdout, help="Output JSONL file")
    command_parser.add_argument('-f', '--format', choices=["csv"], default="csv", help="Which file format to use.")
    command_parser.add_argument('-i', '--input', type=argparse.FileType('r'), default=sys.stdin, help="Input JSONL file")
    command_parser.set_defaults(func=do_import)

    command_parser = subparsers.add_parser('pp', help='Pretty print')
    command_parser.add_argument('-o', '--output', type=argparse.FileType('w'), default=sys.stdout, help="Output JSONL file")
    command_parser.add_argument('-t', '--indent', type=int, default=2, help="Indentation")
    command_parser.add_argument('-i', '--input', type=argparse.FileType('r'), default=sys.stdin, help="Input JSONL file")
    command_parser.set_defaults(func=do_pp)

    command_parser = subparsers.add_parser('extract', help='Extract fields from a JSON')
    command_parser.add_argument('-o', '--output', type=argparse.FileType('w'), default=sys.stdout, help="Output JSONL file")
    command_parser.add_argument('-s', '--schema', type=str, required=True, help="Schema to parse.")
    command_parser.add_argument('-E', '--expand-list', action='store_true', help="Expand lists.")
    command_parser.add_argument('-i', '--input', type=argparse.FileType('r'), default=sys.stdin, help="Input JSONL file")
    command_parser.set_defaults(func=do_extract)

    args = parser.parse_args()
    if args.func is None:
        parser.print_help()
        sys.exit(1)
    else:
        try:
            args.func(args)
        except BrokenPipeError:
            sys.stderr.write("Unexpected broken pipe\n")
            pass

if __name__ == "__main__":
    main()
