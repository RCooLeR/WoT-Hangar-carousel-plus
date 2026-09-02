# -*- coding: utf-8 -*-
"""Fail closed if HCP's private Python hooks no longer match a reviewed client.

Run with Python 2.7. Client bytecode is inspected, never imported or executed.
The contract contains fingerprints only, not Wargaming source or bytecode.
"""
from __future__ import print_function

import argparse
import binascii
import hashlib
import json
import marshal
import os
import sys
import types
import zipfile


def canonical(value):
    if isinstance(value, types.CodeType):
        return ['code', value.co_name, value.co_argcount, value.co_flags,
                binascii.hexlify(value.co_code),
                [canonical(item) for item in value.co_consts],
                list(value.co_names), list(value.co_varnames),
                list(value.co_freevars), list(value.co_cellvars)]
    if isinstance(value, str):
        return ['bytes', binascii.hexlify(value)]
    if isinstance(value, unicode):
        return ['unicode', value]
    if isinstance(value, (tuple, list)):
        return ['sequence', [canonical(item) for item in value]]
    if isinstance(value, frozenset):
        return ['frozenset', sorted(canonical(item) for item in value)]
    if value is None or isinstance(value, (bool, int, long)):
        return value
    if isinstance(value, (float, complex)):
        return [type(value).__name__, repr(value)]
    raise TypeError('Unsupported bytecode constant: %r' % (type(value),))


def fingerprint(code):
    data = json.dumps(canonical(code), ensure_ascii=True, separators=(',', ':'))
    return hashlib.sha256(data.encode('ascii')).hexdigest()


def walk(code, prefix=''):
    key = prefix + code.co_name
    yield key, code
    for child in code.co_consts:
        if isinstance(child, types.CodeType):
            for item in walk(child, key + '.'):
                yield item


def inspect_client(game_root, contract):
    observed = {}
    path = os.path.join(game_root, 'res', 'packages', 'scripts.pkg')
    with zipfile.ZipFile(path) as archive:
        for module, checks in sorted(contract['nodes'].items()):
            payload = archive.read('scripts/client/' + module)
            if payload[:4] != b'\x03\xf3\r\n':
                raise ValueError('Unsupported Python bytecode format: ' + module)
            objects = dict(walk(marshal.loads(payload[8:])))
            observed[module] = {}
            for name in sorted(checks):
                if name not in objects:
                    raise ValueError('Required client hook is missing: %s:%s' % (module, name))
                observed[module][name] = fingerprint(objects[name])
    return observed


def validate(observed, contract):
    failures = []
    for module, checks in sorted(contract['nodes'].items()):
        for name, expected in sorted(checks.items()):
            if observed.get(module, {}).get(name) != expected:
                failures.append('%s:%s' % (module, name))
    if failures:
        raise ValueError('Client API changed; review before building HCP:\n  ' + '\n  '.join(failures))
    return sum(len(checks) for checks in contract['nodes'].values())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--game-root', required=True)
    parser.add_argument('--contract', default=os.path.join(os.path.dirname(__file__), 'client-api-contract.json'))
    parser.add_argument('--describe', action='store_true', help='Print observations for manual review; does not update the contract.')
    args = parser.parse_args()
    with open(args.contract, 'rb') as source:
        contract = json.load(source)
    if contract.get('schemaVersion') != 1:
        raise ValueError('Unsupported API contract schema')
    observed = inspect_client(args.game_root, contract)
    if args.describe:
        print(json.dumps(observed, indent=2, sort_keys=True))
    else:
        print('Validated %d private client API contracts (bytecode was not executed).' % validate(observed, contract))


if __name__ == '__main__':
    try:
        main()
    except (IOError, KeyError, TypeError, ValueError, zipfile.BadZipfile) as error:
        print('Client API validation failed: %s' % error, file=sys.stderr)
        sys.exit(1)
