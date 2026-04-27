#!/usr/bin/env python3
import sys
import pytest

def main():
    rc = pytest.main(['-q'])
    print('\nPYTEST_RETURN_CODE:', rc)
    return rc

if __name__ == '__main__':
    sys.exit(main())
