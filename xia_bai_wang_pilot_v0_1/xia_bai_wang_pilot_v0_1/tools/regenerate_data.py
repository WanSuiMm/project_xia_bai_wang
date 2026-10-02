#!/usr/bin/env python3
"""Reproduce the frozen v0.1 dataset in a separate directory; never contacts a model.

This wrapper deliberately does not regenerate a new study with changed prompts.
The full reproducible builder is tools/build_frozen_bundle.py.
"""
from pathlib import Path
import argparse, subprocess, sys

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', required=True, help='Empty destination directory; never overwrite current dataset.')
    args=p.parse_args(); out=Path(args.output).resolve()
    if out.exists() and any(out.iterdir()):
        p.error('Destination must be empty to protect the frozen pilot.')
    out.mkdir(parents=True,exist_ok=True)
    subprocess.run([sys.executable,str(Path(__file__).with_name('build_frozen_bundle.py')),'--output',str(out)],check=True)

if __name__=='__main__':main()
