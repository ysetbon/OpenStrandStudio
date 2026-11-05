"""The person's tabs: list them, read one as it is now (every strand's points,
masks, undo history and version) or at any step of its history, open a
design in a new tab, rename, switch."""
import json

from .. import project
from ..errors import ToolError

TOOLS = [
    {
        'name': 'list_tabs',
        'description': ("The person's open tabs in OpenStrand Studio: id, title, which one is active, how many "
                        'strands each has, whether it has unsaved changes, its version (changes whenever the '
                        'person edits it) and its undo history (how many steps, which one it is at).'),
        'input_schema': {'type': 'object', 'properties': {}},
    },
    {
        'name': 'read_tab',
        'description': ("Load the design in one of the person's tabs as the current design, as it is right now, "
                        'to describe, change, or make steps from. Gives every strand (name, start, end, control '
                        'points, width, what it is attached to) and mask, the tab\'s version, and its undo history '
                        '(each step and what made it). Nothing in the tab changes. Read it again whenever the person '
                        'may have changed it since (they edit, undo and redo while you work).'),
        'input_schema': {'type': 'object', 'properties': {
            'tab_id': {'type': 'string', 'description': 'from list_tabs'},
        }, 'required': ['tab_id']},
    },
    {
        'name': 'read_tab_step',
        'description': ("Load one step of a tab's undo history as the current design (a copy: the tab does not "
                        'change): what the tab looked like before the person\'s latest changes, or a step they '
                        'undid. read_tab lists the steps and what made each. Gives the same detail as read_tab.'),
        'input_schema': {'type': 'object', 'properties': {
            'tab_id': {'type': 'string', 'description': 'from list_tabs'},
            'step': {'type': 'integer', 'description': 'a step number from read_tab\'s history'},
        }, 'required': ['tab_id', 'step']},
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
LOOK_ONLY = {'list_tabs', 'read_tab', 'read_tab_step'}

INSTRUCTIONS = """- When asked about tabs, use these tools. For how to tie a knot, call tie_knot
  (it makes checked steps), then open_in_new_tab for each step in order, with
  titles like "Step 1 · first loop" that say what the step does. For other
  step-by-step instructions, make the design, call make_steps, then open the
  steps the same way.
- To work on what is in a tab, read_tab it first; it becomes the current design.
  The person keeps working while you do: when they may have changed the tab, or
  an edit is refused because the tab changed, read_tab it again. Use the strand
  names and points read_tab gives, never ones from earlier in the conversation.
- To see the tab before a change, or a step the person undid, read_tab_step
  with a step from read_tab's history.
"""


def list_tabs(agent, args):
    tabs = agent.app.call('list_tabs', {}).get('tabs', [])
    return f'{len(tabs)} tabs', json.dumps(tabs)


def read_tab(agent, args):
    tab = str(args.get('tab_id', ''))
    result, data = read_into_workspace(agent, tab)
    return (f"Read tab {result.get('title', '')} · {project.summary(data)}",
            f"tab \"{result.get('title', '')}\" as it is now (version {result.get('version')}) is the "
            f"current design: {project.summary(data)}\n{project.detail(data)}\n"
            + history_text(result.get('history')))


def read_into_workspace(agent, tab):
    """The tab as it is now becomes the current design, with its version: (result, data)."""
    result = agent.app.call('read_tab', {'tab_id': tab})
    data = project.read(result['file'])
    agent.workspace.store(data, tab=tab, tab_version=result.get('version'))
    return result, data


def read_tab_step(agent, args):
    tab, step = str(args.get('tab_id', '')), args.get('step')
    result = agent.app.call('read_tab_step', {'tab_id': tab, 'step': step})
    data = project.read(result['file'])
    agent.workspace.store(data)  # a copy of a past step: not the tab as it is, so no tab edits from it
    what = f" ({result['what']})" if result.get('what') else ''
    return (f"Tab {result.get('title', '')} at step {result.get('step')} · {project.summary(data)}",
            f"tab \"{result.get('title', '')}\" as it was at undo step {result.get('step')}{what} is now the "
            f"current design (a copy; the tab is at step {result.get('current_step')} of "
            f"{result.get('max_step')} and does not change): {project.summary(data)}\n{project.detail(data)}")


def open_in_new_tab(agent, args):
    ws = agent.workspace
    which = str(args.get('design', 'current')).strip().lower()
    title = str(args.get('title') or '').strip()[:60] or 'Claude design'
    if which in ('current', 'design', ''):
        ws.need()
        path = ws.project_path
    else:
        number = which.replace('step', '').strip()
        if not number.isdigit() or not 1 <= int(number) <= len(ws.steps):
            raise ToolError(f'no {which}: make_steps made {len(ws.steps)} steps')
        path = ws.steps[int(number) - 1][1]
    result = agent.app.call('open_in_new_tab', {'path': str(path), 'title': title})
    if result.get('opened'):
        agent.opened_tabs.append(title)
        return f'New tab · {title}', f'opened in a new tab titled "{title}"'
    return f'{title} · waiting for the person', result.get('note') or 'shown to the person to open'


def rename_tab(agent, args):
    result = agent.app.call('rename_tab', {'tab_id': str(args.get('tab_id', '')),
                                           'title': str(args.get('title') or '').strip()[:60]})
    return f"Rename tab · {result.get('title', '')}", result.get('note') or 'done'


def switch_tab(agent, args):
    result = agent.app.call('switch_tab', {'tab_id': str(args.get('tab_id', ''))})
    return f"Switch tab · {result.get('title', '')}", result.get('note') or 'done'


HANDLERS = {'list_tabs': list_tabs, 'read_tab': read_tab, 'read_tab_step': read_tab_step,
            'open_in_new_tab': open_in_new_tab, 'rename_tab': rename_tab, 'switch_tab': switch_tab}


def history_text(history):
    """A tab's undo history for Claude: which step it is at, what made each step."""
    if not history or not history.get('steps'):
        return 'undo history: none kept'
    lines = [f"undo history (at step {history.get('current_step')} of {history.get('max_step')}; later steps "
             'were undone and can be redone; read_tab_step loads any of them):']
    for step in history['steps'][-40:]:
        lines.append(f"  step {step['step']}{' (now)' if step.get('current') else ''}: {step.get('what') or '-'}")
    return '\n'.join(lines)
