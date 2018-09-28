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
from .util import load_jsonl, list_schema, list_obj

logger = logging.getLogger(__name__)

def do_csv(args):
    writer = csv.writer(args.output, delimiter=args.delimiter)
    data = load_jsonl(args.input)

    datum = next(data)
    header = list_schema(datum)

    writer.writerow(header)
    writer.writerow(list_obj(datum))
   
    for datum in data:
        writer.writerow(list_obj(datum))

def main():
    logging.basicConfig(level=logging.INFO)

    import argparse
    parser = argparse.ArgumentParser(description='jsontool: swiss army knife for JSONL files')
    parser.set_defaults(func=None)

    subparsers = parser.add_subparsers()
    command_parser = subparsers.add_parser('csv', help='Convert to csv')
    command_parser.add_argument('-i', '--input', type=argparse.FileType('r'), default=sys.stdin, help="Input JSONL file")
    command_parser.add_argument('-o', '--output', type=argparse.FileType('w'), default=sys.stdout, help="")
    command_parser.add_argument('-d', '--delimiter', default='\t', help="Delimiter to use to both parse input and write output.")
    command_parser.set_defaults(func=do_csv)

    args = parser.parse_args()
    if args.func is None:
        parser.print_help()
        sys.exit(1)
    else:
        args.func(args)

if __name__ == "__main__":
    main()
