#!/usr/bin/env python3
"""Build helper: attempts to run a quick syntax check on uECC.c using gcc; if gcc is missing,
falls back to using arduino-cli to compile the firmware project.

Usage:
  python tools/build_firmware.py
"""
import shutil
import subprocess
import sys
import os

root = os.path.dirname(os.path.dirname(__file__))
uECC_path = os.path.join(root, 'arduino_firmware', 'third_party', 'uECC', 'uECC.c')

def run(cmd):
    print('> ' + ' '.join(cmd))
    try:
        subprocess.check_call(cmd)
        return True
    except FileNotFoundError:
        return None
    except subprocess.CalledProcessError as e:
        print('Command failed with exit code', e.returncode)
        return False

# 1) Try gcc syntax check if available
gcc = shutil.which('gcc') or shutil.which('clang')
if gcc:
    print('Found C compiler:', gcc)
    if os.path.exists(uECC_path):
        ok = run([gcc, '-fsyntax-only', uECC_path])
        if ok:
            print('Syntax check passed for uECC.c')
        elif ok is False:
            print('Syntax check failed; consider running a full compile with arduino-cli')
        sys.exit(0 if ok else 2)
    else:
        print('uECC.c not found at', uECC_path)
else:
    print('No gcc/clang found on PATH.')

# 2) Fallback: run arduino-cli compile
arduino = shutil.which('arduino-cli')
if arduino:
    print('Found arduino-cli:', arduino)
    print('Attempting to compile entire firmware project (may require network to install cores)')
    ok = run([arduino, 'compile', '--fqbn', 'arduino:avr:mega', os.path.join(root,'arduino_firmware')])
    sys.exit(0 if ok else 3)

# 3) Nothing available: print actionable instructions
print('\nNo suitable C compiler or Arduino CLI found. On Windows, install one of:')
print('  - MSYS2 / MinGW-w64 (for gcc): https://www.msys2.org/')
print('  - Arduino CLI: https://arduino.github.io/arduino-cli/latest/installation/')
print('\nOr run check_build_deps.ps1 for guidance: tools/check_build_deps.ps1')
sys.exit(4)
