"""Entry point for running as a module: python -m linkedin_message_analyzer"""

import sys
from lib.cli import main

if __name__ == '__main__':
    sys.exit(main())
