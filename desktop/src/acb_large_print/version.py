# version.py

# This file provides a single source of truth for the GLOW version.
# All products should read from this file to stay in sync.

def get_version():
    with open('../VERSION', 'r', encoding='utf-8') as f:
        return f.read().strip()
