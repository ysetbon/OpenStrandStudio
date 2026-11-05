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
import contextlib
import json
import queue
import sys
import threading
import time

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
    {
        'name': 'edit_mask_in_tab',
        'description': ("Change one mask in the person's tab, in place, with the app's own code (one undo step; "
                        'in ask mode the person allows it first). The tab must be the one showing and read with '
                        'read_tab first. Same ops and arguments as edit_mask (erase with at, covers, around or '
                        'box; reset; swap; delete; create): the edit is worked out on your copy, checked, then '
                        'done in the tab, and your copy becomes the edited design.'),
        'input_schema': {'type': 'object', 'properties': {
            'tab_id': {'type': 'string', 'description': 'from list_tabs'},
            'op': {'type': 'string', 'enum': ['erase', 'reset', 'swap', 'delete', 'create']},
            'mask': {'type': 'string'}, 'covers': {'type': 'string'},
            'at': {'type': 'array', 'items': {'type': 'number'}},
            'around': {'type': 'array', 'items': {'type': 'number'}}, 'box': {'type': 'array'},
            'first': {'type': 'string'}, 'second': {'type': 'string'},
        }, 'required': ['tab_id', 'op']},
    },
]
APP_TOOL_NAMES = {t['name'] for t in APP_TOOLS}
LOOK_ONLY = {'list_tabs', 'read_tab'}  # what plan mode offers

APP_INSTRUCTIONS = """You are running inside the person's OpenStrand Studio, so you also have tools that
act on the app itself: list_tabs, read_tab, open_in_new_tab, rename_tab,
switch_tab and edit_mask_in_tab, run by the app's own code. OpenStrand Studio has tabs (one design
each), layers grouped in the layer panel, masks for over and under, levels,
arrows on strand ends, end styles, shadows and colors by set.

- When asked about tabs, use these tools. For how to tie a knot, call tie_knot
  (it makes checked steps), then open_in_new_tab for each step in order, with
  titles like "Step 1 · first loop" that say what the step does. For other
  step-by-step instructions, make the design, call make_steps, then open the
  steps the same way.
- To work on what is in a tab, read_tab it first; it becomes the current design.
- After tie_knot, call check_masks, fix each problem with edit_mask (preview
  first when unsure), then render and look before opening the steps.
- When the person points at a mask in their tab (a strand cut off, the wrong
  strand on top at a crossing): read_tab it, check_masks, then either
  edit_mask and open_in_new_tab the fixed design (their tab stays as it is),
  or, when they want their own tab fixed, edit_mask_in_tab (switch_tab to it
  first; it is one undo step). Use the names and coordinates check_masks
  gives, never guessed ones.
- Never say the app cannot do something before checking your tools. If no
  tool does it, do the closest thing you can and tell the person the clicks
  for the rest.
- A tool may answer that the person will open a design or confirm a change
  themselves (they chose to be asked); that is not a failure.

"""


class AppError(Exception):
    pass


class AppClient:
    """Asks the running app to do something, and waits for its answer.

    stdin is read only while a call waits for its answer, one line at a time.
    On Windows a read left waiting on the pipe holds the pipe: anything else
    that looks at it waits for that read to end. Loading numpy's DLLs does (the
    C runtime they bring checks the standard handles as it starts), so with a
    read always waiting, the first knot tool hung for good."""

    def __init__(self, emit, stream=None, timeout=600, log=None):
        self.emit = emit  # writes one event line on stdout
        self.log = log  # the step-by-step log (debuglog.Log), or None
        self.timeout = timeout  # the person may take a while to confirm
        self.stream = stream if stream is not None else sys.stdin
        self.wanted = threading.Semaphore(0)  # one release: read one line
        self.lines = queue.Queue()
        self.closed = False
        self.next_id = 0
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        while True:
            self.wanted.acquire()
            line = self.stream.readline()
            self.lines.put(line)
            if not line:  # the app closed the pipe
                return

    def _line(self, deadline, name):
        if self.closed:
            raise AppError('the app is no longer listening')
        self.wanted.release()
        try:
            line = self.lines.get(timeout=max(0.0, deadline - time.monotonic()))
        except queue.Empty:
            raise AppError(f'the app did not answer {name} in time') from None
        if not line:
            self.closed = True
            raise AppError('the app is no longer listening')
        return line

    def call(self, name, args):
        self.next_id += 1
        call_id = self.next_id
        self.emit({'type': 'app_call', 'id': call_id, 'name': name, 'args': args})
        asked = time.monotonic()
        deadline = asked + self.timeout
        if self.log:
            self.log(f'asking the app #{call_id}: {name} {json.dumps(args)[:200]}')
        waiting = (self.log.waiting(f'the app to answer {name} #{call_id} (in ask mode it waits for Allow or Deny)')
                   if self.log else contextlib.nullcontext())
        with waiting:
            while True:
                line = self._line(deadline, name).strip()
                try:
                    reply = json.loads(line) if line else None
                except ValueError:
                    continue
                if isinstance(reply, dict) and reply.get('id') == call_id:
                    break
        if self.log:
            self.log(f'the app answered #{call_id} in {time.monotonic() - asked:.1f}s: '
                     f'{"ok" if reply.get("ok") else "refused: " + str(reply.get("error"))[:160]}')
        if not reply.get('ok'):
            raise AppError(reply.get('error') or f'the app could not do {name}')
        return reply.get('result') or {}
