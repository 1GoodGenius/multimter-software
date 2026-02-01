#!/usr/bin/env python3
"""Fetch micro-ecc single-file sources into third_party/uECC/ for on-device ECDSA verification.

This script downloads uECC.c and uECC.h from the official micro-ecc repository (MIT licensed).
Run this before building the firmware to enable real ECDSA verification.
"""
import os
import argparse
import urllib.request

BASE_URL = 'https://raw.githubusercontent.com/kmackay/micro-ecc/master/'
FILES = ['uECC.c', 'uECC.h']

parser = argparse.ArgumentParser()
parser.add_argument('--outdir', default=os.path.join('..', 'third_party', 'uECC'), help='Output directory (relative to arduino_firmware/tools)')
args = parser.parse_args()

outdir = os.path.normpath(os.path.join(os.path.dirname(__file__), args.outdir))
if not os.path.isdir(outdir): os.makedirs(outdir, exist_ok=True)

for f in FILES:
    url = BASE_URL + f
    dest = os.path.join(outdir, f)
    print('Downloading', url, '->', dest)
    try:
        urllib.request.urlretrieve(url, dest)
        print('OK')
    except Exception as e:
        print('Failed to download', url, e)

print('\nDone. Now include the files in your Arduino build (they are in arduino_firmware/third_party/uECC).')
