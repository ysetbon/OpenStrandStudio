"""The agent's end of the bridge: asks the running app to do something and
waits for its answer. Each call is one JSON line on stdout,

    {"type": "app_call", "id": 3, "name": "open_in_new_tab", "args": {...}}

and the app (src/agent_bridge, class AppBridge) answers with one line on stdin:

    {"id": 3, "ok": true, "result": {...}}      or      {"id": 3, "ok": false, "error": "..."}
"""
import contextlib
import json
import queue
import sys
import threading
import time


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
