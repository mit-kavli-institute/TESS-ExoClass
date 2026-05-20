#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Merge per-worker cadnoVtimemap_part_w*.txt sidecars produced by
dvts_bulk_resamp.py when run with -n > 1 into a single cadnoVtimemap.txt.

Single-sector sidecars carry a header line:
    # MODE single DATASPAN <span> GDFRAC <frac>
The merger picks the global winner (max DATASPAN + 2*GDFRAC) and copies
its body rows.

Multi-sector sidecars carry:
    # MODE multi
The merger deduplicates cadno across all sidecars (cadno -> time pairs
are identical for the same cadno across files, so first-wins is safe)
and writes the sorted result.

Usage:
    python dvts_cadnomap_merge.py -n 13

The -n value must match the worker count used by dvts_bulk_resamp.py.
"""

import argparse
import glob
import os
import sys


def parse_sidecar(path):
    with open(path, 'r') as f:
        header = f.readline().strip()
        body = f.readlines()
    if not header.startswith('#'):
        raise ValueError(
            '{0}: missing header line (was this written by a single-worker '
            'run? merger expects -n > 1 sidecars)'.format(path))
    tokens = header.lstrip('#').split()
    if len(tokens) < 2 or tokens[0] != 'MODE':
        raise ValueError('{0}: unrecognized header: {1}'.format(path, header))
    mode = tokens[1]
    meta = {}
    if mode == 'single':
        # # MODE single DATASPAN <span> GDFRAC <frac>
        meta['dataspan'] = float(tokens[tokens.index('DATASPAN') + 1])
        meta['gdfrac'] = float(tokens[tokens.index('GDFRAC') + 1])
    return mode, meta, body


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', type=int, required=True,
                        help='Number of workers used by dvts_bulk_resamp.py')
    parser.add_argument('--out', type=str, default='cadnoVtimemap.txt',
                        help='Output filename (default: cadnoVtimemap.txt)')
    args = parser.parse_args()
    nWrk = int(args.n)

    sidecars = sorted(glob.glob('cadnoVtimemap_part_w*.txt'))
    if not sidecars:
        print('No cadnoVtimemap_part_w*.txt sidecars found in cwd.')
        sys.exit(1)

    # The single-sector winner-tracker only writes its sidecar when a target
    # with a new local max is seen; workers whose slice never produced a new
    # max will have no sidecar at all. That's fine for the merge, but warn
    # if we have zero sidecars or more than expected.
    if len(sidecars) > nWrk:
        print('Warning: found {0} sidecars but -n {1}.'.format(
            len(sidecars), nWrk))

    if os.path.isfile(args.out):
        print('{0} EXISTS! Remove or rename it before merging.'.format(args.out))
        sys.exit(1)

    modes = set()
    parsed = []
    for sc in sidecars:
        mode, meta, body = parse_sidecar(sc)
        modes.add(mode)
        parsed.append((sc, mode, meta, body))

    if len(modes) != 1:
        print('Sidecars disagree on mode: {0}'.format(modes))
        sys.exit(1)
    mode = modes.pop()

    if mode == 'single':
        # Pick global winner by dataSpan + 2*gdFrac.
        def score(item):
            _, _, meta, _ = item
            return meta['dataspan'] + 2.0 * meta['gdfrac']

        winner = max(parsed, key=score)
        sc, _, meta, body = winner
        print('Single-sector winner: {0} (DATASPAN={1:f} GDFRAC={2:f})'.format(
            sc, meta['dataspan'], meta['gdfrac']))
        with open(args.out, 'w') as f:
            f.writelines(body)
    else:
        # Multi-sector: dedup cadno across all sidecars, sort.
        cad_to_line = {}
        for _, _, _, body in parsed:
            for line in body:
                parts = line.split()
                if not parts:
                    continue
                cad = int(parts[0])
                if cad not in cad_to_line:
                    cad_to_line[cad] = line
        with open(args.out, 'w') as f:
            for cad in sorted(cad_to_line.keys()):
                f.write(cad_to_line[cad])
        print('Multi-sector: merged {0} unique cadences from {1} sidecars.'.format(
            len(cad_to_line), len(parsed)))


if __name__ == '__main__':
    main()
