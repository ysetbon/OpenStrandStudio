"""The bridge between Claude and the running OpenStrand Studio.

Claude's agent runs in its own process (python -m openstrand agent --app) and
cannot reach the app's windows. When it calls one of its app tools it writes
a request line on stdout; the Claude panel hands it to AppBridge.handle, on
the app's main thread, and writes the answer back to the agent's stdin (see
openstrand/app/ for the other end).

Each action is a few lines over the app's own code, one module per area:

- tabs.py     list, read (as it is now, or any undo step), open, rename, switch
- strands.py  move a strand's ends and handles (Move mode's code, as a drag)
- masks.py    erase, reset, swap, delete, create masks (the canvas's mask code)
- layers.py   everything the layer panel's right-click menu does
- groups.py   everything the group panel does
- core.py     AppBridge: runs a request by its Action, following the panel's mode
- base.py     BridgeError, Action, and what every area shares

What runs follows the panel's mode: in plan mode Claude may only look; in ask
mode a change waits for the person's Allow or Deny (a design waits as a card
they open); in auto mode it happens. Every edit of a tab names the tab's
version it was worked out on, and is refused when the person changed the tab
since, so Claude never edits from an out-of-date copy.
"""
from .base import BridgeError
from .core import AppBridge

__all__ = ['AppBridge', 'BridgeError']
