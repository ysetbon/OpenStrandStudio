"""What every area of the bridge shares: errors, how an action is declared,
and the lookups and the undo step its code needs."""
from dataclasses import dataclass


class BridgeError(Exception):
    """A request the app cannot do: its message goes back to Claude."""


@dataclass(frozen=True)
class Action:
    """How the bridge runs one action. Names are methods of AppBridge.

    run    method(args, session) -> result dict
    change it changes something: never in plan mode; in ask mode the person decides
    tab    it takes a tab_id (the session is looked up for it)
    edits  it edits the tab showing: must be that tab, is checked against the
           version Claude read, and answers with the tab's new version
    check  method(args, session): refuses a bad request before the person is asked
    card   method(args, session) -> (kind, tab title, what): the Allow/Deny card
    ask    method(args, session) -> result: what ask mode does instead of a card
    """
    run: str
    change: bool = False
    tab: bool = False
    edits: bool = False
    check: str = None
    card: str = None
    ask: str = None


class BridgeBase:
    def __init__(self, window, panel):
        self.window = window
        self.panel = panel
        self.pending = {}  # call id -> the call, waiting for the person's Allow or Deny

    @property
    def canvas(self):
        return self.window.canvas

    @property
    def tabs(self):
        manager = getattr(self.window, 'tab_manager', None)
        if manager is None:
            raise BridgeError('this window has no tabs')
        return manager

    def session(self, tab_id):
        session = self.tabs.find(str(tab_id or ''))
        if session is None:
            raise BridgeError(f'no tab {tab_id}: list_tabs gives the ids')
        return session

    def require_showing(self, session):
        """Edits work on the tab showing (the live canvas)."""
        if session.id != self.tabs.active_tab_id:
            raise BridgeError(f'"{self.tabs.title_for(session)}" is not the tab showing: switch_tab to it first')

    def strand(self, name):
        for s in self.canvas.strands:
            if s.layer_name == str(name or '') and not hasattr(s, 'get_mask_path'):
                return s
        raise BridgeError(f'there is no strand {name} in this tab')

    def mask(self, name):
        for s in self.canvas.strands:
            if s.layer_name == str(name or '') and hasattr(s, 'get_mask_path'):
                return s
        raise BridgeError(f'there is no mask {name} in this tab')

    def layer(self, name):
        """A strand or a mask: a row of the layer panel."""
        for s in self.canvas.strands:
            if s.layer_name == str(name or ''):
                return s
        raise BridgeError(f'there is no layer {name} in this tab')

    def save_undo(self, action, targets):
        """One undo step for what Claude just did, named so the history says so."""
        manager = getattr(self.canvas, 'undo_redo_manager', None)
        if manager is not None:
            manager._last_save_time = 0
            manager.save_state(action=action, source='claude', targets=[t for t in targets if t])
