#!/usr/bin/env python
from infrared.main import main
import sys


if __name__ == '__main__':
    sys.exit(int(main() or 0))
