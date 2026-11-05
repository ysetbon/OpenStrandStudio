import os
import sys

from .cli import main

code = main()
# Leave without Python's teardown: with the app's hidden Qt window still
# alive, tearing down the interpreter can crash the process after the work
# is done and saved, turning a success into a failed exit.
sys.stdout.flush()
sys.stderr.flush()
os._exit(code)
