"""The agent's step-by-step log, to see what a request is doing and where it waits.

Every call to Claude (how long it took, why it stopped, tokens, cost), every
tool (its input, how long it ran) and every question to the app, with the
time since the request started. While something takes long, a line every
WAIT_EVERY seconds says what it is still waiting for, so a request that seems
stuck shows whether Claude is still thinking, a tool is running or the app
has not answered.

Lines go to agent.log in the request's folder and, when asked, to stderr: the
real one, kept aside, since tools run with stderr pointed at nothing (quiet()).
Each line starts with PREFIX, so a reader can tell them from errors.
"""
import contextlib
import os
import sys
import threading
import time

PREFIX = 'log '
WAIT_EVERY = 30.0  # seconds between "still waiting" lines


class Log:
    def __init__(self, path=None, to_stderr=False, clock=time.monotonic):
        self.clock = clock
        self.started = clock()
        self.lock = threading.Lock()
        self.outs = []
        if path is not None:
            try:
                self.outs.append(open(path, 'a', encoding='utf-8', buffering=1))
            except OSError:
                pass  # no log file: the stderr copy still works
        if to_stderr:
            try:
                sys.stderr.flush()
                self.outs.append(os.fdopen(os.dup(sys.stderr.fileno()), 'w', encoding='utf-8',
                                           newline='\n', buffering=1))
            except (AttributeError, OSError, ValueError):
                self.outs.append(sys.stderr)

    def __call__(self, text):
        line = f'{PREFIX}{time.strftime("%H:%M:%S")} +{self.clock() - self.started:7.1f}s  {text}'
        with self.lock:
            for out in self.outs:
                try:
                    out.write(line + '\n')
                    out.flush()
                except (OSError, ValueError):
                    pass

    @contextlib.contextmanager
    def waiting(self, what, every=None):
        """While the block runs: a line every `every` seconds saying it still waits for what."""
        every = WAIT_EVERY if every is None else every
        done = threading.Event()
        since = self.clock()

        def remind():
            while not done.wait(every):
                self(f'... still waiting for {what}: {self.clock() - since:.0f}s')

        thread = threading.Thread(target=remind, daemon=True)
        thread.start()
        try:
            yield
        finally:
            done.set()


class NoLog:
    """No log: the same calls, doing nothing."""

    def __call__(self, text):
        pass

    def waiting(self, what, every=None):
        return contextlib.nullcontext()


def short(value, size=300):
    """A value for one log line: one line, cut to size."""
    text = ' '.join(str(value).split())
    return text if len(text) <= size else text[:size - 1] + '…'
