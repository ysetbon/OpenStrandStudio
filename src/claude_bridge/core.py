"""AppBridge: runs one request from Claude by the Action its area declares."""
from .base import BridgeBase, BridgeError
from .groups import GroupActions
from .layers import LayerActions
from .masks import MaskActions
from .strands import StrandActions
from .tabs import TabActions

AREAS = (TabActions, StrandActions, MaskActions, LayerActions, GroupActions)


class AppBridge(TabActions, StrandActions, MaskActions, LayerActions, GroupActions, BridgeBase):
    ACTIONS = {name: spec for area in AREAS for name, spec in area.ACTIONS.items()}

    def handle(self, call):
        """Answer one request: a reply dict, or None when the person decides later."""
        call_id, name, args = call.get('id'), call.get('name'), call.get('args') or {}
        try:
            spec = self.ACTIONS.get(name)
            if spec is None:
                raise BridgeError(f'the app has no action {name}')
            mode = self.panel.run_mode
            if spec.change and mode == 'plan':
                raise BridgeError('plan mode is on: Claude may look at tabs but not change them')
            session = self.session(args.get('tab_id')) if spec.tab else None
            self.check(spec, args, session)
            if spec.change and mode == 'ask':
                if spec.ask:
                    return self.ok(call_id, getattr(self, spec.ask)(args, session))
                self.pending[call_id] = call
                self.panel.add_confirm_card(call_id, getattr(self, spec.card)(args, session))
                return None
            return self.ok(call_id, self.run(spec, args, session))
        except BridgeError as e:
            return self.fail(call_id, str(e))
        except Exception as e:  # the app's own code failed: tell Claude, keep the app running
            return self.fail(call_id, f'{type(e).__name__}: {e}')

    def decide(self, call_id, allowed):
        """The person's Allow or Deny for a waiting change: the reply to send."""
        call = self.pending.pop(call_id, None)
        if call is None:
            return None
        if not allowed:
            return self.fail(call_id, 'the person declined this change')
        try:
            spec, args = self.ACTIONS[call['name']], call.get('args') or {}
            session = self.session(args.get('tab_id')) if spec.tab else None
            self.check(spec, args, session)  # again: the person may have changed the tab while deciding
            return self.ok(call_id, self.run(spec, args, session))
        except BridgeError as e:
            return self.fail(call_id, str(e))
        except Exception as e:
            return self.fail(call_id, f'{type(e).__name__}: {e}')

    def check(self, spec, args, session):
        if spec.edits:
            self.require_showing(session)
            self.check_fresh(args, session)
        if spec.check:
            getattr(self, spec.check)(args, session)

    def run(self, spec, args, session):
        result = getattr(self, spec.run)(args, session)
        if spec.edits:
            result = dict(result, version=self.version(session))
        return result

    def forget(self):
        """The agent has stopped: nothing is waiting any more."""
        self.pending.clear()

    @staticmethod
    def ok(call_id, result):
        return {'id': call_id, 'ok': True, 'result': result}

    @staticmethod
    def fail(call_id, error):
        return {'id': call_id, 'ok': False, 'error': error}
