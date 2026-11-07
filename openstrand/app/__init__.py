"""Tools that act on the person's running OpenStrand Studio, one module per area.

The agent runs in its own process, so it cannot touch the app's windows. When
the app starts it (with --app), these tools go through a bridge instead
(client.py here, src/claude_bridge in the app): each call is a JSON line on
stdout, and the app runs it with its own code and answers on stdin.

- client.py   AppClient: the bridge's agent end
- tabs.py     list, read (as it is now, or any undo step), open, rename, switch
- strands.py  move a strand's ends and handles in a tab
- masks.py    edit masks in a tab
- layers.py   the layer panel's right-click menu
- groups.py   the group panel
- window.py   the main window's buttons: toolbar, beside the canvas, under the layer panel
- settings.py the Settings dialog: read, set, show a page

Each area declares TOOLS (the schemas Claude sees), LOOK_ONLY (the ones plan
mode offers), INSTRUCTIONS (its part of what Claude is told) and HANDLERS
(name -> function(agent, args) returning (summary for people, content for
Claude)). The app decides what is allowed: in plan mode only looking, in ask
mode the person confirms changes.
"""
from . import groups, layers, masks, settings, strands, tabs, window
from .client import AppClient, AppError

AREAS = (tabs, strands, masks, layers, groups, window, settings)
APP_TOOLS = [tool for area in AREAS for tool in area.TOOLS]
APP_TOOL_NAMES = {tool['name'] for tool in APP_TOOLS}
LOOK_ONLY = set().union(*(area.LOOK_ONLY for area in AREAS))  # what plan mode offers
HANDLERS = {name: handler for area in AREAS for name, handler in area.HANDLERS.items()}

APP_INSTRUCTIONS = (
    """You are running inside the person's OpenStrand Studio, so you also have tools that
act on the app itself, run by the app's own code: """ + ', '.join(t['name'] for t in APP_TOOLS) + """.
OpenStrand Studio has tabs (one design each), layers grouped in the layer panel,
masks for over and under, levels, arrows on strand ends, end styles, shadows and
colors by set.

""" + ''.join(area.INSTRUCTIONS for area in AREAS) + """- Never say the app cannot do something before checking your tools. If no
  tool does it, do the closest thing you can and tell the person the clicks
  for the rest.
- A tool may answer that the person will open a design or confirm a change
  themselves (they chose to be asked); that is not a failure.

""")

__all__ = ['AppClient', 'AppError', 'APP_TOOLS', 'APP_TOOL_NAMES', 'LOOK_ONLY', 'HANDLERS', 'APP_INSTRUCTIONS']
