"""Tools that act on the person's running OpenStrand Studio: its tabs.

The agent runs in its own process, so it cannot touch the app's windows. When
the app starts it (with --app), these tools go through a bridge instead: each
call is written as a JSON line on stdout,

    {"type": "app_call", "id": 3, "name": "open_in_new_tab", "args": {...}}

and the app runs it with its own code (src/claude_bridge.py, class AppBridge)
and answers with one JSON line on stdin:

    {"id": 3, "ok": true, "result": {...}}      or      {"id": 3, "ok": false, "error": "..."}

The app decides what is allowed: in plan mode only looking, in ask mode the
person confirms changes.
"""
import json
import queue
import sys
import threading

APP_TOOLS = [
    {
        'name': 'list_tabs',
        'description': ("The person's open tabs in OpenStrand Studio: id, title, which one is active, how many "
                        'strands each has, and whether it has unsaved changes.'),
        'input_schema': {'type': 'object', 'properties': {}},
    },
    {
        'name': 'read_tab',
        'description': ("Load the design in one of the person's tabs as the current design, to describe, change, "
                        'or make steps from. Nothing in the tab changes.'),
        'input_schema': {'type': 'object', 'properties': {
            'tab_id': {'type': 'string', 'description': 'from list_tabs'},
        }, 'required': ['tab_id']},
    },
    {
        'name': 'open_in_new_tab',
        'description': ("Open a design made in this request in a new tab of the person's app, with a title. "
                        'design is "current" (the current design) or "step N" (from make_steps). The '
                        "person's other tabs stay as they are. Open steps in order, one call each."),
        'input_schema': {'type': 'object', 'properties': {
            'design': {'type': 'string', 'description': '"current" or "step 1", "step 2", ...'},
            'title': {'type': 'string', 'description': 'the tab title, short, e.g. "Step 1 · first loop"'},
        }, 'required': ['design', 'title']},
    },
    {
        'name': 'rename_tab',
        'description': "Give one of the person's tabs a new title.",
        'input_schema': {'type': 'object', 'properties': {
            'tab_id': {'type': 'string'}, 'title': {'type': 'string'},
        }, 'required': ['tab_id', 'title']},
    },
    {
        'name': 'switch_tab',
        'description': "Show one of the person's tabs.",
        'input_schema': {'type': 'object', 'properties': {'tab_id': {'type': 'string'}}, 'required': ['tab_id']},
    },
]
APP_TOOL_NAMES = {t['name'] for t in APP_TOOLS}
LOOK_ONLY = {'list_tabs', 'read_tab'}  # what plan mode offers

APP_INSTRUCTIONS = """You are running inside the person's OpenStrand Studio, so you also have tools that
act on the app itself: list_tabs, read_tab, open_in_new_tab, rename_tab and
switch_tab, run by the app's own code. OpenStrand Studio has tabs (one design
each), layers grouped in the layer panel, masks for over and under, levels,
arrows on strand ends, end styles, shadows and colors by set.

- When asked about tabs, use these tools. For step-by-step instructions, make
  the design, call make_steps, then open_in_new_tab for each step in order,
  with titles like "Step 1 · first loop" that say what the step adds.
- To work on what is in a tab, read_tab it first; it becomes the current design.
- Never say the app cannot do something before checking your tools. If no
  tool does it, do the closest thing you can and tell the person the clicks
  for the rest.
- A tool may answer that the person will open a design or confirm a change
  themselves (they chose to be asked); that is not a failure.

"""


class AppError(Exception):
    pass


class AppClient:
    """Asks the running app to do something, and waits for its answer."""

    def __init__(self, emit, stream=None, timeout=600):
        self.emit = emit  # writes one event line on stdout
        self.timeout = timeout  # the person may take a while to confirm
        self.replies = queue.Queue()
        self.next_id = 0
        stream = stream if stream is not None else sys.stdin
        threading.Thread(target=self._read, args=(stream,), daemon=True).start()

    def _read(self, stream):
        for line in stream:
            line = line.strip()
            if not line:
                continue
            try:
                self.replies.put(json.loads(line))
            except ValueError:
                continue
        self.replies.put(None)  # the app closed the pipe

    def call(self, name, args):
        self.next_id += 1
        call_id = self.next_id
        self.emit({'type': 'app_call', 'id': call_id, 'name': name, 'args': args})
        while True:
            try:
                reply = self.replies.get(timeout=self.timeout)
            except queue.Empty:
                raise AppError(f'the app did not answer {name} in time') from None
            if reply is None:
                self.replies.put(None)
                raise AppError('the app is no longer listening')
            if reply.get('id') == call_id:
                break
        if not reply.get('ok'):
            raise AppError(reply.get('error') or f'the app could not do {name}')
        return reply.get('result') or {}
