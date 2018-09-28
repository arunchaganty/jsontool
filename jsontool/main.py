#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSONtool
"""
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
from .util import load_jsonl, list_schema, list_obj, JsonWriter

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


def main():
    logging.basicConfig(level=logging.INFO)

    import argparse
    parser = argparse.ArgumentParser(description='jsontool: swiss army knife for JSONL files')
    parser.set_defaults(func=None)

    subparsers = parser.add_subparsers()
    command_parser = subparsers.add_parser('csv', help='Convert to csv')
    command_parser.add_argument('-i', '--input', type=argparse.FileType('r'), default=sys.stdin, help="Input JSONL file")
    command_parser.add_argument('-o', '--output', type=argparse.FileType('w'), default=sys.stdout, help="Output CSV file")
    command_parser.add_argument('-d', '--delimiter', default='\t', help="Delimiter to use to both parse input and write output.")
    command_parser.set_defaults(func=do_csv)

    command_parser = subparsers.add_parser('filter', help='Filter to csv')
    command_parser.add_argument('-i', '--input', type=argparse.FileType('r'), default=sys.stdin, help="Input JSONL file")
    command_parser.add_argument('-o', '--output', type=argparse.FileType('w'), default=sys.stdout, help="Output JSONL file")
    command_parser.add_argument('-e', '--exprs', type=str, nargs="+", required=True, help="Filter expressions.")
    command_parser.add_argument('-a', '--all', action="store_true", help="Do all expressions have to match?")
    command_parser.set_defaults(func=do_filter)

    command_parser = subparsers.add_parser('extract', help='Extract fields from a JSON')
    command_parser.add_argument('-i', '--input', type=argparse.FileType('r'), default=sys.stdin, help="Input JSONL file")
    command_parser.add_argument('-o', '--output', type=argparse.FileType('w'), default=sys.stdout, help="Output JSONL file")
    command_parser.add_argument('-e', '--exprs', type=str, nargs="+", required=True, help="Filter expressions.")
    command_parser.add_argument('-a', '--all', action="store_true", help="Do all expressions have to match?")
    command_parser.set_defaults(func=do_filter)

    args = parser.parse_args()
    if args.func is None:
        parser.print_help()
        sys.exit(1)
    else:
        args.func(args)

if __name__ == "__main__":
    main()
