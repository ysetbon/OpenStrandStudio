"""An agent that builds OpenStrand Studio projects with the openstrand tools.

The agent loop is ours: the agent reads the request (and any reference image),
researches it on the web when it needs to, plans a structure, builds it from
samples, generators or its own drawing, looks at each render, and stops when
the design is right. Everything it does is reported through on_event, one
dict per step, so a terminal or the app's agent panel can show progress.

Runs with the user's own API key for the model's provider (ANTHROPIC_API_KEY for Claude).
"""
import base64
import contextlib
import json
import mimetypes
import sys
import time
from pathlib import Path

from . import ROOT, colors, edit, generators, project
from .debuglog import short
from .errors import ToolError  # agent.ToolError: what a tool raises for the agent

from . import providers

# Every model the agent runs on (openstrand/providers.py): Claude, GPT, Grok, Kimi, DeepSeek, Qwen.
MODELS = dict(providers.ALIASES)  # 'sonnet', 'haiku', 'grok', ... -> the model id
DEFAULT_MODEL = providers.DEFAULT_MODEL
EFFORTS = ('low', 'medium', 'high', 'xhigh', 'max')

# USD per million tokens: input, output, cache write (5 min), cache read.
# Haiku 5.5's prices are for prompts up to 100K tokens, which these stay under.
PRICES = providers.PRICES
WEB_SEARCH_PRICE = 0.01  # USD per search ($10 per 1,000)

# Server-side fallback re-runs a declined Sonnet request on another model;
# Haiku has none.
FALLBACK_BETA = 'server-side-fallback-2026-07-01'

# Web tools run on Anthropic's servers. Sonnet 5.5 has the versions that
# filter results before they reach the context; Haiku 5.5 the basic ones.
WEB_TOOLS = {
    'claude-sonnet-5-5': [{'type': 'web_search_20260209', 'name': 'web_search', 'max_uses': 6},
                          {'type': 'web_fetch_20260209', 'name': 'web_fetch', 'max_uses': 6}],
    'claude-haiku-5-5': [{'type': 'web_search_20250305', 'name': 'web_search', 'max_uses': 6},
                         {'type': 'web_fetch_20250910', 'name': 'web_fetch', 'max_uses': 6}],
}

SKILL = ROOT / '.claude' / 'skills' / 'openstrand-designer'
GUIDE = SKILL / 'guide.md'
DRAWING = SKILL / 'drawing.md'

INSTRUCTIONS = """You design OpenStrand Studio projects for the person you are talking to.
OpenStrand Studio is a desktop app for drawing knots, mats, stitches and other
woven strand designs. Every design you make goes through the tools, so it opens
in the app with real strands, masks and groups.

How to work:
1. Understand the request from the words and any reference image. Describe an
   image in the guide's terms first (kind of design, loops, crossings, colors).
   A request to make, show or explain a knot, stitch or pattern, or a tutorial
   or "how to" for one, asks for a design: build it with the tools in this same
   request. Never answer with written steps alone, and never end by offering
   to draw it: draw it. Words alone answer a question (what is this, why did
   that happen), not a request to make something. When a tool cannot do the
   exact thing, make the closest design you can and say in one sentence what
   differs.
2. Look it up first: call search_samples with the person's own words for the
   thing (its name, its craft). A match says what it is and ends with the tool
   call that makes it: make that call. If a published sample or a make_ tool
   fits, use it: it is the fastest and cleanest result.
3. Otherwise design it yourself:
   - Research: when you do not know exactly what the thing is or how it is
     tied or woven, search the web (web_search) and read a good page
     (web_fetch): its structure, how many strands, how they cross, what it
     looks like when finished.
   - If the web has nothing useful, reason it out from first principles: what
     the name suggests, how similar knots and stitches are built. Say what you
     assumed.
   - Plan the structure in OpenStrand terms: how many cords, where each runs,
     where they cross, which goes over.
   - Draw it with draw_design, using the drawing guide below. Read the report:
     crossings, conflicts and warnings.
4. Call render and look at the picture. Compare it with the request and with
   what you learned: counts, shape, colors, over and under. Fix what is off and
   draw or render again. Stop after five renders.
5. Finish with two or three short sentences: what you made, how it is built,
   and anything you could not do or had to assume. Plain words, no markdown.

Knots (how one is tied, or one shown tied):
- knot_library lists every knot tie_knot makes by name, of two kinds. Stopper
  knots tied in one cord (overhand, figure-eight, double overhand, stevedore,
  triple overhand): tie_knot works their steps out by simulating a real cord,
  laid out move by move and pulled tight. Knots that join cords or make a
  loop (square or reef knot, granny knot, sheet bend, fisherman's knot, which
  knitters call the magic knot, double fisherman's knot, bowline, macrame
  square knot): tie_knot draws their steps from a checked drawing, the knot
  shown loose. Either way it checks every step is that knot, crossing by
  crossing, also as drawn in the app.
- The craft library has more knots tie_knot ties the same way, from checked
  drawings with their steps (macrame hitches and sennits, Chinese knots,
  braids): search_samples finds them by any name and ends with the tie_knot
  call to make.
- So for any knot in knot_library, call tie_knot with its name, at once: do
  not search the web for it first. Such a knot is not yours to draw:
  never draw tying steps or a tightened knot by hand, nor the knot itself
  with draw_design. A freehand drawing of a bowline or a square knot comes
  out as some other knot.
- A knot in one cord that is not in knot_library: research how it is tied,
  then give tie_knot its path (rough points from the standing end, crossing
  itself where the knot does, a few cord widths between parts) and its
  over/under pattern. Read the checks: they name the knot the path makes. If
  it is not the knot you meant, fix the path or the pattern and try again.
- For the knot in a design the person already has (in the app: read_tab it
  first), call tie_knot with from_design: it keeps that knot's over and under.
- A loop knot or a knot that joins two cords (a bend) that is not in
  knot_library (a zeppelin bend, a water knot): research it, then draw it
  with draw_design, loose enough to follow, one cord per rope, each in its
  own color and labeled. Such knots seldom alternate, so say which cord is on
  top: give a cord a "pattern", a letter for each crossing it passes in order
  from its start, O over or U under. The report lists each cord's crossings
  in that order with the pattern as drawn: to turn a crossing over, change
  its letter and draw again (never with edit_mask). Then check it with
  identify_knot: it names only the ready-made knots, so for any other knot it
  tells you how the cords cross, not that the drawing is that knot. Tell the
  person such a drawing is your own sketch and has not been checked against
  the real knot. For a tutorial or how to tie it, then call make_steps: it
  shows the cords drawn bit by bit, in the order you list them, so list first
  the cord that is laid down first; it says what each step shows, to title
  the tabs by (how much of each cord, where its end is). Use draw_steps
  instead when the cords must move between the pictures (see below). Say in
  one sentence
  that these steps are drawn, not simulated. If the drawing is still not
  exactly the knot when you stop, keep the closest one, make and open its
  steps all the same, and say which part differs: a sketch with its steps is
  what the person asked for, not an apology.
- To check any design is the knot it should be, call identify_knot rather than
  judging the picture. It names a ready-made knot from its crossings, or says
  which crossings go the other way round; for cords that cross each other it
  says how often, which is on top, and whether one passes through a loop of
  the other. A cord that lies over another everywhere is not joined to it.

Step-by-step pictures (tutorials, "how to", "the next steps"):
- Three tools make steps; choose by what changes from one picture to the next.
  tie_knot: any knot in knot_library, stopper knots, bends and loop knots;
  checked step by step.
  make_steps: one finished design shown as it is drawn, bit by bit. Nothing
  moves, more of it appears: a mat, a weave, a bend drawn loose.
  draw_steps: every picture is its own drawing. Use it whenever the cord moves
  between pictures: a loop is pulled through, an end is tucked, a knot is drawn
  up, a hook, needle or finger works the cord, an arrow shows the next move.
  That is every crochet and knitting stitch (chain, slip stitch, single and
  double crochet, casting on), a slip knot, a hitch on a post, a loop knot not
  in knot_library, and "what comes after this step".
- For draw_steps, first plan the pictures in words: what each shows, what
  moved since the one before, the tool and the arrow in it. Three to six
  steps, one move each; the last shows the finished thing. Then send them all
  in ONE draw_steps call, never one draw_design per picture: a hook is a tool
  ({"tool": "hook", ...}) and an arrow is an arrow ("arrows"), never cords
  drawn to look like them.
- In each step give only what is new: "keep" the cords that did not move,
  redraw (same label) the one that did. Give every cord that crosses another
  its heights, so the picture shows what really lies on top: a hook goes into
  a loop over one side of it and under the other.
- An arrow in a step shows the move that leads to the next step, starting
  where the cord or the hook is now and ending where it will be.
- draw_steps answers with one picture of all the steps. Check each against
  your plan, then fix only the steps that are off with "replace". Stop after
  three rounds and say what still differs.
- A reference image with numbered or separate pictures: one step per picture,
  in its order, each showing what that picture shows.
- A slip knot is not an overhand knot: pulling its working end undoes it, so
  identify_knot finds no knot in the yarn of a right one ("no knot: the cord
  would slip free"; with a hook in the picture, "not knotted on its own").
  The guide has it drawn step by step; start from that.

Masks (which strand is on top at a crossing) in tight and crowded designs:
- A tight knot's parts touch and its joints sit inside crossings, so a mask
  can paint over a strand beside its crossing, or a crossing can show half one
  way, half the other. tie_knot already fixes what is safe and lists what is
  left per step ("masks fixed", "masks left"). The same happens in any crowded
  design: stretched MxN stitches, Turk's heads with a small inner radius,
  designs whose cords lie close together.
- After tie_knot (and after drawing or loading anything crowded), call
  check_masks. For each problem it lists, call the edit_mask it names, with
  preview: true first when unsure; use its coordinates and names, never guess
  them. Prefer covers (uncover a strand) and around (one crossing) over a box:
  the tool shapes those along the strand's outline. Then render and look
  closely at each place you changed. Stop when check_masks finds nothing, or
  say what is left and why (some places need the strands moved apart).
  Not needed for a knot tie_knot drew loose from a checked drawing (a bend, a
  loop knot): its result says every mask is right. Render that one and look.
- Where a problem says neither the design nor a mask says which strand goes
  over, the check reads it from what most of the crossing shows: compare with
  the render and with what the person asked before you change it.

Drawing a design or its steps, tying a knot, making a heart or a Turk's head
size that is not published each take a few seconds; the person sees the tool's progress. Call it
once and wait.

"""

# Plan mode: research and plan, build nothing. Only tools that look are offered.
PLAN_TOOLS = ('search_samples', 'describe', 'knot_library', 'identify_knot', 'check_masks')
PLAN_INSTRUCTIONS = """Plan mode is on: the person wants a plan before anything is built. The
tools that build are not available, so do not try to build. Research as much as
you need (samples, the web, the current design), then answer with a short plan
in plain words, as a numbered list: what the design is and how it is built in
the real world; the cords and how each runs; where they cross and which goes
over; the colors; and how you will build it (which sample or make_ tool, or
draw_design and the curve for each cord). End with any question the person
should answer before you build. No markdown headings or bold.

"""

# The parts draw_design and draw_steps share (openstrand/draw.py reads them).
CORD = {'type': 'object', 'description': 'one cord: points, x/y, shape or tool, plus style and heights'}
ARROW = {'type': 'object', 'description': 'an arrow: {"points": [[x, y], ...]} from its tail to its head, '
                                          'plus optional color (default red) and label'}
STEP = {'type': 'object', 'properties': {
    'step': {'type': 'integer', 'description': 'in "replace" only: the number of the step this one replaces'},
    'title': {'type': 'string', 'description': 'what the step does, short: "Pull the yarn through the loop"'},
    'keep': {'description': 'labels of the cords that stay exactly as in the step before, or "all"'},
    'cords': {'type': 'array', 'maxItems': 12, 'items': CORD,
              'description': 'the cords new in this step, and those of the step before that moved (same label)'},
    'arrows': {'type': 'array', 'maxItems': 8, 'items': ARROW,
               'description': 'the move that leads to the next step'}},
    'required': ['title']}

TOOLS = [
    {
        'name': 'search_samples',
        'description': 'Look up ready-made designs. First the craft library, found by any name people use '
                       '(boondoggle, scoubidou, box stitch, macrame, cobra knot, Chinese knotting, mystic knot, '
                       'knitting, magic knot, crochet, any knot by name): each match says what it is and the '
                       'exact tool call that makes it. Then the published files whose names contain the text '
                       '(knots, Turk\'s heads, links, MxN stitches). Empty text lists the crafts and all files.',
        'input_schema': {'type': 'object', 'properties': {
            'text': {'type': 'string', 'description': 'what the person asked for in a few words, e.g. '
                                                      '"box stitch", "chinese knot", "turks", "mxn_rh"'}},
            'required': ['text']},
    },
    {
        'name': 'load_sample',
        'description': 'Start from a ready-made design by its name (from search_samples): a published file '
                       'or a craft library entry.',
        'input_schema': {'type': 'object', 'properties': {'name': {'type': 'string'}}, 'required': ['name']},
    },
    {
        'name': 'make_turks_head',
        'description': "Make a woven Turk's head ring knot. Leads (2-7) and bights (2-13) must share "
                       "no common factor. Published sizes are instant; others take a few seconds.",
        'input_schema': {'type': 'object', 'properties': {
            'leads': {'type': 'integer', 'description': 'turns around the ring'},
            'bights': {'type': 'integer', 'description': 'loops on the rim'},
            'color': {'type': 'string', 'description': 'color name or hex; default teal'}},
            'required': ['leads', 'bights']},
    },
    {
        'name': 'make_mxn',
        'description': 'Make an MxN stitch: m vertical and n horizontal ribbons (each 1-8). '
                       'Each ribbon is its own set.',
        'input_schema': {'type': 'object', 'properties': {
            'm': {'type': 'integer'}, 'n': {'type': 'integer'},
            'hand': {'type': 'string', 'enum': ['lh', 'rh'], 'description': 'left or right hand; default lh'},
            'stretch': {'type': 'boolean', 'description': 'ribbons packed closer together'}},
            'required': ['m', 'n']},
    },
    {
        'name': 'make_heart',
        'description': 'Make a ribbon heart from one cord, its ends crossing below the tip. Takes a few seconds.',
        'input_schema': {'type': 'object', 'properties': {
            'color': {'type': 'string', 'description': 'color name or hex; default crimson'}}},
    },
    {
        'name': 'draw_design',
        'description': 'Draw your own design from cord centerlines; it replaces the current design. '
                       'Each cord is points it passes through ({"points": [[x, y], ...]}), a parametric '
                       'curve ({"x": "...t...", "y": "...t...", "t0": 0, "t1": "2*pi"}), a shape '
                       '({"shape": "circle", "center": [x, y], "radius": r}; also ellipse, polygon, heart, '
                       'turks_head) or a tool ({"tool": "hook", "from": [x, y], "to": [x, y]}; also needle, '
                       'stick), plus optional closed, color, width, label, second_color, tucked, pattern, '
                       'heights. Every crossing gets over and under, alternating along each cord, unless a '
                       'cord has a pattern: a letter for each crossing it passes, in order from its start, O '
                       'over or U under ("-" leaves one to the other cord), for knots that do not alternate; '
                       'or, between cords given heights, the higher one on top. "arrows" are drawn on top and '
                       'never woven. Send the whole design every time. Returns a report: every crossing and '
                       'which cord is on top, each cord\'s crossings in order with its pattern as drawn '
                       '(change a letter and draw again to turn that crossing over), conflicts and warnings. '
                       'One picture only: for a tutorial of several pictures use draw_steps. See "Drawing '
                       'your own designs" in the guide.',
        'input_schema': {'type': 'object', 'properties': {
            'name': {'type': 'string', 'description': 'what the design is'},
            'weave': {'type': 'string', 'enum': ['alternate', 'alternate_under_first']},
            'cords': {'type': 'array', 'minItems': 1, 'maxItems': 12, 'items': CORD},
            'arrows': {'type': 'array', 'maxItems': 8, 'items': ARROW}},
            'required': ['cords']},
    },
    {
        'name': 'draw_steps',
        'description': ('Draw a tutorial whose pictures differ from step to step, all of it in one call: a crochet '
                        'or knitting stitch, a slip knot, a hitch or loop knot shown stage by stage, anything '
                        'where the cord moves between the pictures or a hook, a needle or an arrow is in them. '
                        'Each step is its own drawing: a title, its cords (as in draw_design: points, x/y or '
                        'shape; "heights" or "height" say what lies on top), tools as cords ({"tool": "hook" | '
                        '"needle" | "stick", "from": [x, y], "to": [x, y]}: a straight stick, "to" is its tip) '
                        'and arrows ({"points": [[x, y], ...]}, tail first: red, on top of everything, never '
                        'woven: the move to make next). A step says only what is new: "keep" lists the labels of '
                        'the cords that stay exactly as in the step before; a cord with a label of the step '
                        'before is that cord redrawn. Returns a report per step (crossings, what is on top, '
                        'masks) and one picture of all the steps side by side. Saves them as "step 1", "step 2", '
                        '... (open them with open_in_new_tab); the last becomes the current design. To fix or '
                        'add steps afterwards, send only those in "replace". See "Steps drawn one by one" in '
                        'the guide.'),
        'input_schema': {'type': 'object', 'properties': {
            'name': {'type': 'string', 'description': 'what the tutorial shows'},
            'steps': {'type': 'array', 'minItems': 1, 'maxItems': 12, 'items': STEP,
                      'description': 'the whole sequence, in order'},
            'replace': {'type': 'array', 'minItems': 1, 'maxItems': 12, 'items': STEP,
                        'description': 'after a first call: only the steps to change, each with "step": its '
                                       'number (the number after the last adds a step); the others stay as sent'}}},
    },
    {
        'name': 'tie_knot',
        'description': ('Steps to tie a knot, each a checked design. Knots in knot_library by name: a stopper '
                        'knot in one cord (overhand, figure-eight, ...) is worked out by simulating a real cord: '
                        'laid out move by move with an arrow on the working end, drawn up, then pulled tight '
                        'until it touches itself. A knot that joins cords or makes a loop (square or reef knot, '
                        'granny, sheet bend, fisherman\'s or magic knot, double fisherman\'s, bowline, macrame '
                        'square knot) comes from a checked drawing, shown loose, cord by cord with an arrow on '
                        'the working end. Every step is checked to be that knot from its crossings, also as '
                        'drawn in the app. A knot in one cord that is not in the library: from its path, rough '
                        '[x, y] points from the standing end to the working end, crossing itself where the knot '
                        'does, and its over/under pattern; or the knot in the current design (from_design, e.g. '
                        'after read_tab). A path or a design is tightened by pulling its two ends apart, as for '
                        'stopper knots; a loop knot or a bend that is not in the library cannot be given that '
                        'way: draw those with draw_design, then make_steps for the steps (or draw_steps). Saves '
                        'the steps as '
                        '"step 1", "step 2", ... (open them with open_in_new_tab) and makes the finished knot '
                        'the current design. Library knots take a few seconds; a path or a design a few more '
                        '(a path drawn larger than it needs is shrunk to a laid-out size first). The person '
                        'sees its progress live.'),
        'input_schema': {'type': 'object', 'properties': {
            'knot': {'type': 'string', 'description': 'a library knot, by any name people use: "bowline", '
                                                      '"square knot", "magic knot", "figure-eight"'},
            'points': {'type': 'array', 'items': {'type': 'array', 'items': {'type': 'number'}},
                       'description': 'for a knot in one cord that is not in the library: its path, standing '
                                      'end first'},
            'pattern': {'type': 'string', 'description': 'with points: O or U for each crossing the path '
                                                         'passes, in order along it (default alternating)'},
            'from_design': {'type': 'boolean', 'description': 'tie the knot of the current design (one open '
                                                              'cord), keeping its over and under'},
            'color': {'type': 'string', 'description': 'color name or hex; default teal'},
            'colors': {'type': 'array', 'items': {'type': 'string'},
                       'description': 'for a knot of several cords: one color for each (default teal, gold)'},
            'width': {'type': 'number', 'description': 'cord width in px: 16-60 for a knot in one cord '
                                                       '(default 24), 14-30 for a knot of several cords'},
            'moves': {'type': 'integer', 'minimum': 1, 'maximum': 6,
                      'description': 'a knot in one cord: tying pictures before it is drawn up (default: up '
                                     'to 4)'}}},
    },
    {
        'name': 'knot_library',
        'description': 'The knots tie_knot makes by name: stopper knots in one cord, and knots that join '
                       'cords or make a loop (square knot, sheet bend, fisherman\'s knot, bowline, ...); the '
                       'names people use, crossings, what each is for.',
        'input_schema': {'type': 'object', 'properties': {}},
    },
    {
        'name': 'identify_knot',
        'description': ('Which knot the current design shows, read from its strands, masks and layers the way '
                        'the app draws them. First the ready-made knot it is (square knot, sheet bend, bowline, '
                        'fisherman\'s knot, ...) when every crossing goes as in that knot\'s checked drawing, or '
                        'which crossings go the other way round. Then per cord its crossings, its pattern (O '
                        'over, U under, in order along it) and its knot type on its own (an open cord is named '
                        'as if its ends were joined high above it, as for a tied rope); and, for a design of a '
                        'few cords, how each two cross: how often, which is on top, whether one passes through '
                        'a loop of the other. Use it to check that a design really is the knot it should be, '
                        'instead of judging by eye.'),
        'input_schema': {'type': 'object', 'properties': {}},
    },
    {
        'name': 'check_masks',
        'description': ('Check the masks of the current design, measured with the app\'s own paths and clipping: '
                        'every mask (its two strands, which is on top, its centre, its erase boxes) and every '
                        'problem, located with canvas coordinates: a mask piece painting over a strand that should '
                        'show (covers_strand), part of a crossing showing the strand that should be under '
                        '(wrong_way), a mask covering two crossings of its strands where one should be the other way '
                        '(two_crossings), a crossing drawn the other way round from the design (wrong_crossing). '
                        'Each problem names the edit_mask call that fixes it. Changes nothing. Needed after '
                        'tie_knot (tight knots: parts touch, joints sit inside crossings) and for any crowded '
                        'design: tight knots, stretched MxN stitches, Turk\'s heads with small inner radius.'),
        'input_schema': {'type': 'object', 'properties': {}},
    },
    {
        'name': 'edit_mask',
        'description': ('Change one mask of the current design with the app\'s own code, then check again '
                        '(identify and check_masks) and report. op: "erase" adds erase boxes, shaped by the tool '
                        'to follow a strand\'s outline; give one of: at [x, y] (a problem check_masks listed '
                        'there: just that place is erased), covers (a strand: the mask is erased where it paints '
                        'over it), around [x, y] (the mask\'s whole piece at that crossing), box ([x0, y0, x1, '
                        'y1] or four [x, y] corners) when you know the exact area. "reset" is Reset Mask (every '
                        'erase box gone). "swap" puts the other strand on top (delete and create reversed; its '
                        'erase boxes go). "delete" removes the mask. "create" masks two strands (first on top of '
                        'second). create and swap trim the new mask at once wherever it would paint the wrong '
                        'way. preview: true shows the result and the check after it without keeping it. '
                        'Otherwise the edited design becomes the current design.'),
        'input_schema': {'type': 'object', 'properties': {
            'op': {'type': 'string', 'enum': ['erase', 'reset', 'swap', 'delete', 'create']},
            'mask': {'type': 'string', 'description': 'the mask name, as check_masks lists it, e.g. "1_1_1_6"'},
            'at': {'type': 'array', 'items': {'type': 'number'},
                   'description': 'erase: [x, y] where check_masks listed a problem of this mask'},
            'covers': {'type': 'string', 'description': 'erase: the strand the mask should stop covering'},
            'around': {'type': 'array', 'items': {'type': 'number'}, 'description': 'erase: [x, y] of a crossing'},
            'box': {'type': 'array', 'description': 'erase: [x0, y0, x1, y1] or four [x, y] corners'},
            'first': {'type': 'string', 'description': 'create: the strand on top'},
            'second': {'type': 'string', 'description': 'create: the strand under it'},
            'preview': {'type': 'boolean', 'description': 'show what the edit would do, keep nothing'}},
            'required': ['op']},
    },
    {
        'name': 'describe',
        'description': 'Describe the current design: each set with its color and which way it runs '
                       '(vertical, horizontal), strands, masks, size.',
        'input_schema': {'type': 'object', 'properties': {}},
    },
    {
        'name': 'recolor',
        'description': 'Give the listed sets one color (name or hex). Masks follow their sets.',
        'input_schema': {'type': 'object', 'properties': {
            'sets': {'type': 'array', 'items': {'type': 'integer'}, 'description': 'set numbers, e.g. [1, 2, 3]'},
            'color': {'type': 'string'}},
            'required': ['sets', 'color']},
    },
    {
        'name': 'validate',
        'description': "Load the current design with the app's own loader and list problems.",
        'input_schema': {'type': 'object', 'properties': {}},
    },
    {
        'name': 'render',
        'description': "Draw the current design with the app's real canvas and return the picture to look at. "
                       'With step, one of the steps instead (tie_knot, make_steps, draw_steps), full size.',
        'input_schema': {'type': 'object', 'properties': {
            'step': {'type': 'integer', 'description': 'a step number, to look at that step'}}},
    },
    {
        'name': 'make_steps',
        'description': ('Turn the current design into tying steps: step k shows the cord drawn so far along its '
                        'path, every crossing with its finished over and under, and an arrow on the working end '
                        'showing where the cord goes next; the last step is the whole design. Each step is saved '
                        'as its own design ("step 1", "step 2", ...) that can open in its own tab. Says what '
                        'each step shows: how much of each cord, and where the working end is. Default: one '
                        'step per strand, at most six.'),
        'input_schema': {'type': 'object', 'properties': {
            'count': {'type': 'integer', 'minimum': 2, 'maximum': 12, 'description': 'how many steps'},
            'arrows': {'type': 'boolean', 'description': 'arrow on the working end (default true)'},
        }},
    },
]



# The long edge, in px, of the largest picture a model reads whole (Claude Sonnet 5.5 and
# Haiku 5.5; the API shrinks a larger one to this itself). A larger file only makes every
# round's upload slower, and past 10 MB the API refuses it: a phone's photo is 4,000 px.
MAX_EDGE = 2576


def shrunk(path):
    """A picture larger than MAX_EDGE, made that size: (media type, bytes). None for one
    that already fits, or that Qt cannot read (it is then sent as it is)."""
    try:
        from PyQt5.QtCore import QBuffer, QIODevice, Qt
        from PyQt5.QtGui import QImageReader
    except ImportError:
        return None
    reader = QImageReader(str(path))
    reader.setAutoTransform(True)  # a photo taken sideways stays upright once it is saved again
    size = reader.size()
    if max(size.width(), size.height()) <= MAX_EDGE:
        return None
    image = reader.read()
    if image.isNull():
        return None
    image = image.scaled(MAX_EDGE, MAX_EDGE, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    kind, quality = ('PNG', -1) if image.hasAlphaChannel() else ('JPEG', 90)
    buffer = QBuffer()
    buffer.open(QIODevice.WriteOnly)
    if not image.save(buffer, kind, quality):
        return None
    return f'image/{kind.lower()}', bytes(buffer.data())


def image_block(path):
    """A user-message image block for a PNG, JPEG, GIF or WebP file."""
    path = Path(path)
    media = mimetypes.guess_type(path.name)[0]
    if media not in ('image/png', 'image/jpeg', 'image/gif', 'image/webp'):
        raise ValueError(f'{path}: use a PNG, JPEG, GIF or WebP image')
    media, raw = shrunk(path) or (media, path.read_bytes())
    data = base64.standard_b64encode(raw).decode('ascii')
    return {'type': 'image', 'source': {'type': 'base64', 'media_type': media, 'data': data}}


def reference_images(model, paths):
    """The request's reference pictures as image blocks, no more than the model takes
    (providers.image_limit)."""
    paths = list(paths)
    limit, label = providers.image_limit(model), providers.MODELS[model].label
    if paths and not limit:
        raise ValueError(f'{label} cannot see pictures: leave the images out, or use another model')
    if len(paths) > limit:
        raise ValueError(f'{label} takes up to {limit} reference images with one request ({len(paths)} given)')
    return [image_block(p) for p in paths]


def _searches(usage):
    server = getattr(usage, 'server_tool_use', None)
    return (getattr(server, 'web_search_requests', 0) or 0) if server is not None else 0


def cost_of(model, usage):
    """USD for one response's usage, web searches included."""
    p_in, p_out, p_write, p_read = PRICES.get(model, PRICES[DEFAULT_MODEL])
    get = lambda name: getattr(usage, name, 0) or 0
    return ((get('input_tokens') * p_in + get('output_tokens') * p_out
             + get('cache_creation_input_tokens') * p_write
             + get('cache_read_input_tokens') * p_read) / 1_000_000
            + _searches(usage) * WEB_SEARCH_PRICE)


class Workspace:
    """The design being built, saved to out_dir after every change."""

    def __init__(self, out_dir):
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.project_path = self.out_dir / 'design.json'
        self.png_path = self.out_dir / 'design.png'
        self.data = None
        self.tab = None
        self.tab_version = None
        self.theirs = False  # the current design is the person's own, as read (never shared as the agent's)
        self.own = False  # this request read a design of the person's (its work is then never called new)
        self.version = 0
        self.rendered_version = -1
        self._preview = None
        self._shot, self._shots = None, 0  # (version, path) of the current design's last picture; pictures made
        self.steps = []  # [(title, path)] from make_steps, tie_knot or draw_steps
        self.story = None  # the steps draw_steps was sent last, as sent: "replace" changes single ones
        self.sheet = None  # (version, path) of the picture of all of draw_steps' steps
        self.last_edit = None  # the design edit_mask made last (kept or previewed)
        self.progress = None  # set while a tool runs: tells the person how far it has got

    def need(self):
        if self.data is None:
            raise ToolError('there is no design yet: make, draw or load one first')
        return self.data

    def store(self, data, tab=None, tab_version=None, theirs=False):
        """data becomes the current design. theirs: it is the person's own as read (their canvas,
        a tab, a past step of one), not this request's work, until a tool stores another."""
        self.data = data
        self.tab = tab  # the tab this design was read from, while it is unchanged
        self.tab_version = tab_version  # that tab's version when read: edits are refused if it changed
        self.theirs = bool(theirs or tab is not None)
        self.own = self.own or self.theirs  # from here on, what it makes may come from theirs
        self.version += 1
        project.write(data, self.project_path)

    def render(self, step=None):
        """The current design's picture, or one step's (its number), full size."""
        from generate_creative_samples import AppPreview
        if step is not None:
            if isinstance(step, bool) or not isinstance(step, int) or not 1 <= step <= len(self.steps):
                raise ToolError(f'no step {step}: there are {len(self.steps)} steps')
            data, path = project.read(self.steps[step - 1][1]), self.out_dir / f'step_{step}.png'
        else:
            data, path = self.need(), self.png_path
        generators.application()
        if self._preview is None:
            self._preview = AppPreview()
        from . import render
        render.capture(self._preview, data, path)
        if step is None:
            self.rendered_version = self.version
        return path

    def draw_steps(self, args):
        """Every step of a tutorial drawn in one call: (summary, content with
        one picture of all of them)."""
        from . import storyboard
        if args.get('steps') is not None:
            story = args['steps']
        elif args.get('replace') is not None:
            story = storyboard.replace(self.story, args['replace'])
        else:
            raise ToolError('give "steps" (the whole sequence), or "replace" (the steps to change of the '
                            'sequence sent before)')
        if isinstance(story, list):
            self.story = story  # kept even when a step fails: "replace" then fixes just that step
        made = storyboard.build({'steps': story, 'weave': args.get('weave')}, progress=self.progress)
        self.steps = []
        for number, step in enumerate(made, start=1):
            path = self.out_dir / f'step_{number}.json'
            project.write(step['data'], path)
            self.steps.append((step['title'], path))
        self.store(made[-1]['data'])
        count = len(made)
        text = (storyboard.summary(made) + f'\nSaved as "step 1" to "step {count}"; the current design is step '
                f'{count}. The picture shows them all, in order: check each one against what the step should '
                'show (what crosses over what, where the hook and the arrows are, that it leads on from the '
                'step before). Fix a step that is off with draw_steps "replace" (only that step); render with '
                '"step" shows one step larger. In the app, open each with open_in_new_tab, in order, titled '
                'by what it does, e.g. "Step 1 · make a loop".')
        content = [{'type': 'text', 'text': text}]
        self.sheet = None
        try:
            pictures = [self.snapshot(step['data']) for step in made]
            sheet = storyboard.sheet(pictures, [step['title'] for step in made], self.out_dir / 'steps.png')
            self.sheet = (self.version, sheet)
            data = base64.standard_b64encode(sheet.read_bytes()).decode('ascii')
            content.append({'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': data}})
        except Exception as e:  # noqa: BLE001 - the steps are drawn and saved: say so, without the picture
            content[0]['text'] += f'\n(No picture of the steps: {type(e).__name__}: {e}. Use render with "step".)'
        title = str(args.get('name') or 'steps')[:40]
        return f'{title} · {count} step{"s" if count != 1 else ""}', content

    def snapshot(self, data=None):
        """A picture of a design (the current one by default) for the tool's row in the
        app: drawn with the app's real canvas, cut to the design with a margin. The
        current design is drawn once per version. Returns the PNG's path."""
        from . import render
        current = data is None
        data = self.need() if current else data
        if current and self._shot is not None and self._shot[0] == self.version and self._shot[1].exists():
            return self._shot[1]
        from generate_creative_samples import AppPreview
        generators.application()
        if self._preview is None:
            self._preview = AppPreview()
        frames = self.out_dir / 'frames'
        frames.mkdir(exist_ok=True)
        self._shots += 1
        path = frames / f'tool_{self._shots}.png'
        render.shot(self._preview, data, path)
        if current:
            self._shot = (self.version, path)
        return path

    def close(self):
        if self._preview is not None:
            self._preview.close()
            self._preview = None

    def edit_mask(self, args, store=True):
        """One mask edit on the current design: (summary, text); the edited
        design becomes the current one unless previewed (it is in last_edit)."""
        from . import identify, masks
        op = str(args.get('op') or '')
        try:
            new, done = masks.edit(self.need(), op, mask=args.get('mask'), first=args.get('first'),
                                   second=args.get('second'), box=args.get('box'), covers=args.get('covers'),
                                   around=args.get('around'), at=args.get('at'))
            found = masks.check(new)
        except masks.MaskError as e:
            raise ToolError(str(e)) from None
        preview = bool(args.get('preview'))
        if store and not preview:
            self.store(new)
        count = len(found['problems'])
        head = ('Preview, not kept: ' if preview else '') + done
        text = '\n'.join([head, 'Knot: ' + identify.summary(new), found['text']]
                         + ([] if preview else ['This is now the current design: render it and look.']))
        summary = f"{'Preview · ' if preview else ''}{done[:60]} · {count} problem{'s' if count != 1 else ''} left"
        self.last_edit = new
        return summary, text

    def tie_drawn(self, args):
        """tie_knot for a knot that joins cords or makes a loop (bends.LIBRARY):
        its steps from the checked drawing, the finished knot the current design."""
        from . import bends
        given = args.get('colors') or ([args['color']] if args.get('color') else None)
        try:
            made = bends.tie(args.get('knot'), colors=given, width=args.get('width'), progress=self.progress)
        except (bends.BendError, ImportError) as e:
            raise ToolError(str(e)) from None
        self.steps = []
        for number, step in enumerate(made['steps'], start=1):
            path = self.out_dir / f'step_{number}.json'
            project.write(step['data'], path)
            self.steps.append((step['title'], path))
        self.store(made['steps'][-1]['data'])
        count = len(made['steps'])
        lines = [f"{made['title']}: {bends.KINDS[made['kind']]}, {made['crossings']} crossings. {made['about']}"]
        lines.append('Checks: ' + bends.checked(made))
        if not made['ok']:
            lines.append('WARNING: not every step came out as the knot; tell the person which step is off.')
        lines.append('These steps are drawn from the checked drawing, not simulated: the knot is shown loose, as '
                     'it is tied. Say so in one sentence.')
        for number, step in enumerate(made['steps'], start=1):
            lines.append(f"step {number}: {step['caption']}")
        lines.append(f'Saved as "step 1" to "step {count}"; the current design is the finished knot (step '
                     f'{count}). In the app, open each step with open_in_new_tab, in order, titled by what it '
                     'does, e.g. "Step 1 · the bight".')
        return f"{made['title']} · {count} steps", '\n'.join(lines)

    def search_samples(self, text):
        """Craft library entries that match, each with the call that makes it, then file names."""
        from . import library
        text = text.strip()
        lines = []
        entries = library.search(text) if text else []
        if entries:
            lines.append('Craft library (each line ends with the tool call that makes it):')
            lines += [library.line(e) for e in entries[:12]]
            if len(entries) > 12:
                lines.append(f'(and {len(entries) - 12} more: search with more words)')
        elif not text:
            lines.append('Craft library, by craft (search a craft or a name to see its designs):')
            lines += [f'{craft}: {about}' for craft, about in library.crafts().items()]
        names = [n for n in generators.samples() if text.lower() in n.lower()]
        if names:
            lines.append('Published files (load_sample name): ' + ', '.join(names[:60])
                         + (f' (and {len(names) - 60} more)' if len(names) > 60 else ''))
        if not entries and not names:
            return '0 samples', ('nothing matches; try one word of the name, or a craft (boondoggle, macrame, '
                                 'chinese knotting, knitting, crochet, knots)')
        return f'{len(entries) + len(names)} samples', '\n'.join(lines)

    def run(self, name, args):
        """Do one tool call. Returns (summary for people, content for the agent)."""
        if name == 'search_samples':
            return self.search_samples(str(args.get('text', '')))
        if name == 'load_sample':
            data, _, source = generators.sample(str(args.get('name', '')))
            self.store(data)
            return f'{source} · {project.summary(data)}', f'loaded {source}: {project.summary(data)}'
        if name == 'make_turks_head':
            color = colors.parse(args.get('color') or 'teal')
            data, warnings, source = generators.turks_head(int(args['leads']), int(args['bights']), color)
            self.store(data)
            note = f' (from the published sample {source})' if source else ''
            text = f"Turk's head {args['leads']}x{args['bights']}: {project.summary(data)}{note}"
            if warnings:
                text += '; warnings: ' + '; '.join(' '.join(map(str, w)) for w in warnings)
            return f"Turk's head {args['leads']}×{args['bights']} · {project.summary(data)}", text
        if name == 'make_mxn':
            data, _, source = generators.mxn(int(args['m']), int(args['n']), args.get('hand') or 'lh',
                                             bool(args.get('stretch')))
            self.store(data)
            return f"Stitch {args['m']}×{args['n']} {args.get('hand') or 'lh'} · {project.summary(data)}", \
                f'made {source}: {project.summary(data)}'
        if name == 'make_heart':
            data, warnings, _ = generators.heart(colors.parse(args.get('color') or 'crimson'))
            self.store(data)
            return f'Heart · {project.summary(data)}', f'made a ribbon heart: {project.summary(data)}'
        if name == 'draw_design':
            from . import draw
            data, report = draw.build(args, progress=self.progress)
            self.store(data)
            title = str(args.get('name') or 'drawing')[:40]
            return f'{title} · {project.summary(data)}', report + '\nNow render it and look at the result.'
        if name == 'draw_steps':
            return self.draw_steps(args)
        if name == 'tie_knot':
            from . import bends, tying
            wanted = args.get('knot')
            if wanted and not args.get('from_design') and not args.get('points') and tying.find(wanted) is None:
                if bends.find(wanted) is not None:
                    return self.tie_drawn(args)
                raise ToolError(f'"{wanted}" is not in the knot library (knot_library lists them: '
                                + ', '.join([r['title'] for r in tying.LIBRARY.values()]
                                            + [r['title'] for r in bends.LIBRARY.values()])
                                + '). A knot tied in one cord can be given as its path: points from the standing '
                                'end, with its over/under pattern. A knot that joins cords or makes a loop is '
                                'drawn with draw_design, a pattern on each cord, then make_steps.')
            cord = None
            if args.get('from_design'):
                from . import identify
                try:
                    cord = identify.cord_of(self.need())
                except ValueError as e:
                    raise ToolError(str(e)) from None
            try:
                made = tying.tie(knot=args.get('knot') if cord is None else None, points=args.get('points'),
                                 pattern=args.get('pattern'), width=args.get('width') or tying.DEFAULT_WIDTH,
                                 color=colors.parse(args.get('color') or 'teal'), count=args.get('moves'),
                                 cord=cord, progress=self.progress)
            except (tying.TyingError, ImportError) as e:
                raise ToolError(str(e)) from None
            self.steps = []
            for number, step in enumerate(made['steps'], start=1):
                path = self.out_dir / f'step_{number}.json'
                project.write(step['data'], path)
                self.steps.append((step['title'], path))
            self.store(made['steps'][-1]['data'])
            name_ = made['knot'] or f"a knot with Alexander polynomial {made['alexander']}"
            lines = [f"{made['title']}: {name_}, {made['crossings']} crossings."]
            lines.append('Checks (knot type at each stage): ' + '; '.join(
                f"{c['stage']}: {c['knot'] or c['alexander']}" for c in made['checks']))
            if not made['ok']:
                lines.append('WARNING: not every stage is the same knot; tell the person which step is off.')
            for number, step in enumerate(made['steps'], start=1):
                lines.append(f"step {number}: {step['caption']}")
                found = step.get('masks')
                if found:
                    for text in found['fixed']:
                        lines.append(f'  masks fixed: {text}')
                    for p in found['left']:
                        lines.append(f"  masks left: {p['text']}")
                    if not found['fixed'] and not found['left']:
                        lines.append('  masks: no problems')
            lines.append(f'Saved as "step 1" to "step {len(made["steps"])}"; the current design is the tight '
                         'knot. In the app, open each step with open_in_new_tab, in order, titled by what it '
                         'does, e.g. "Step 1 · first loop".')
            return f"{made['title']} · {len(made['steps'])} steps", '\n'.join(lines)
        if name == 'check_masks':
            from . import masks
            try:
                found = masks.check(self.need())
            except masks.MaskError as e:
                raise ToolError(str(e)) from None
            count = len(found['problems'])
            unsure = f" · {len(found['unsure'])} unsure" if found['unsure'] else ''
            return (f"{len(found['masks'])} masks · {count} problem{'s' if count != 1 else ''}{unsure}", found['text'])
        if name == 'edit_mask':
            return self.edit_mask(args)
        if name == 'knot_library':
            from . import bends, tying
            lines = ['Stopper knots, tied in one cord (tie_knot simulates the cord, laid out and pulled tight):']
            lines += [f'{title} ("{key}"): {crossings} crossings, {kind}; also called {", ".join(aliases)}. {about}'
                      for key, title, crossings, kind, aliases, about in tying.library()]
            lines.append('Knots that join cords or make a loop (tie_knot draws them from a checked drawing, '
                         'shown loose):')
            lines += [f'{title} ("{key}"): {kind}, {crossings} crossings; also called {", ".join(aliases)}. '
                      f'{about}' for key, title, kind, _, crossings, aliases, about in bends.library()]
            return f'{len(lines) - 2} knots', '\n'.join(lines)
        if name == 'identify_knot':
            from . import identify
            text = identify.summary(self.need(), unknown=True)
            return text.splitlines()[0][:80], text
        if name == 'describe':
            info = project.describe(self.need())
            lines = [f"{info['strands']} strands, {info['masks']} masks, size {info['size'][0]}x{info['size'][1]}"]
            for n, s in info['sets'].items():
                lines.append(f"set {n}: {s['strands']} strands, {' '.join(s['colors'])}"
                             + (f", runs {s['runs']}" if s['runs'] else ''))
            return project.summary(self.need()), '\n'.join(lines)
        if name == 'recolor':
            sets = [int(n) for n in args.get('sets') or []]
            if not sets:
                raise ToolError('list at least one set number')
            color = colors.parse(str(args.get('color', '')))
            data = self.need()
            edit.recolor(data, {n: color for n in sets})
            self.store(data)
            return f"Sets {', '.join(map(str, sets))} → {color}", f"recolored sets {sets} to {color}"
        if name == 'validate':
            from . import check
            found = check.problems(self.need())
            if found:
                return f'{len(found)} problems', 'problems:\n' + '\n'.join(found)
            return 'valid', f'valid: {project.summary(self.data)}'
        if name == 'make_steps':
            from . import steps
            made = steps.make(self.need(), count=args.get('count'), arrows=args.get('arrows', True) is not False)
            self.steps = []
            for number, (title, data) in enumerate(made, start=1):
                path = self.out_dir / f'step_{number}.json'
                project.write(data, path)
                self.steps.append((title, path))
            lines = [f'made {len(made)} steps; the last is the whole design. What each shows, to title its tab '
                     'by (a cord is drawn from its first point on):']
            lines += [f'step {number}: {text}' for number, text in enumerate(steps.shown(made), start=1)]
            lines.append('Each can open in its own tab with open_in_new_tab if you are running in the app.')
            return f'{len(made)} steps', '\n'.join(lines)
        if name == 'render':
            path = self.render(args.get('step'))
            data = base64.standard_b64encode(path.read_bytes()).decode('ascii')
            return 'picture', [{'type': 'image', 'source': {'type': 'base64', 'media_type': 'image/png', 'data': data}}]
        raise ToolError(f'unknown tool {name}')


class Agent:
    """Runs one request: the loop of model calls and tool calls."""

    def __init__(self, client, out_dir, model=DEFAULT_MODEL, on_event=None, max_rounds=24, max_cost=2.00,
                 quiet=None, web=True, effort='high', plan=False, app=None, log=None):
        if model not in PRICES:
            raise ValueError(f"model must be one of {', '.join(PRICES)}")
        if effort not in EFFORTS:
            raise ValueError(f"effort must be one of {', '.join(EFFORTS)}")
        self.client = client
        # Wraps every tool call; the CLI passes one that hides the app's own
        # console output, so it cannot mix with the events.
        self.quiet = quiet or contextlib.nullcontext
        self.model = model
        self.label = providers.MODELS[model].label
        # Web search and fetch are Anthropic's server tools: Claude only.
        self.web = web and providers.provider_of(model).api == 'anthropic'
        self.effort = effort
        self.plan = plan  # plan mode: research and plan, build nothing
        self.app = app  # an AppClient when the app started the agent: its tabs become tools
        from .debuglog import NoLog
        self.log = log or NoLog()  # the step-by-step log (debuglog.Log), for debugging a request
        self.opened_tabs = []  # titles of tabs opened by open_in_new_tab
        self.workspace = Workspace(out_dir)
        self.on_event = on_event or (lambda event: None)
        self.max_rounds = max_rounds
        self.max_cost = max_cost
        self.cost = 0.0
        self.searches = 0
        self.usage = {'input_tokens': 0, 'output_tokens': 0,
                      'cache_creation_input_tokens': 0, 'cache_read_input_tokens': 0}

    def system(self):
        from .app import APP_INSTRUCTIONS
        text = (INSTRUCTIONS + (APP_INSTRUCTIONS if self.app else '') + (PLAN_INSTRUCTIONS if self.plan else '')
                + 'The guide:\n\n' + GUIDE.read_text(encoding='utf-8')
                + '\n\n' + DRAWING.read_text(encoding='utf-8'))
        return [{'type': 'text', 'text': text, 'cache_control': {'type': 'ephemeral'}}]

    def tools(self):
        from .app import APP_TOOLS, LOOK_ONLY
        tools = [t for t in TOOLS if t['name'] in PLAN_TOOLS] if self.plan else list(TOOLS)
        if self.app is not None:
            tools += [t for t in APP_TOOLS if t['name'] in LOOK_ONLY] if self.plan else APP_TOOLS
        return tools + (WEB_TOOLS.get(self.model, []) if self.web else [])

    def call(self, messages):
        params = dict(model=self.model, max_tokens=20000, system=self.system(), tools=self.tools(),
                      messages=messages, thinking={'type': 'adaptive', 'display': 'summarized'},
                      output_config={'effort': self.effort})
        try:
            if self.model == MODELS['sonnet']:
                return self.client.beta.messages.create(betas=[FALLBACK_BETA], fallbacks='default', **params)
            return self.client.messages.create(**params)
        except Exception as e:
            # An organization can switch the web tools off for its API keys:
            # carry on without them rather than fail the request.
            text = str(e)
            if self.web and getattr(e, 'status_code', None) == 400 and ('web_search' in text or 'web_fetch' in text):
                self.web = False
                self.log('web tools refused for this API key: continuing without them')
                self.on_event({'type': 'note', 'text': 'Web search is not available for this API key '
                                                        '(an organization setting in the Anthropic Console); '
                                                        'continuing without it.'})
                return self.call(messages)
            self.log(f'the {providers.provider_of(self.model).name} API failed: {type(e).__name__}: {short(e)}')
            raise

    def count(self, response):
        for key in self.usage:
            self.usage[key] += getattr(response.usage, key, 0) or 0
        self.searches += _searches(response.usage)
        self.cost += cost_of(self.model, response.usage)
        self.on_event({'type': 'usage', 'cost': round(self.cost, 4), 'searches': self.searches, **self.usage})

    def report(self, block):
        """Events for the parts of a response people want to follow."""
        kind = block.type
        if kind == 'thinking' and (getattr(block, 'thinking', '') or '').strip():
            self.on_event({'type': 'thinking', 'text': block.thinking.strip()})
        elif kind == 'server_tool_use':
            args = block.input if isinstance(block.input, dict) else {}
            self.on_event({'type': 'search', 'name': block.name,
                           'query': args.get('query') or args.get('url') or ''})
        elif kind in ('web_search_tool_result', 'web_fetch_tool_result'):
            content = getattr(block, 'content', None)
            error = getattr(content, 'error_code', None) if not isinstance(content, list) else None
            found = len(content) if isinstance(content, list) else None
            self.on_event({'type': 'search_result', 'name': kind.replace('_tool_result', ''),
                           'ok': error is None, 'error': error, 'results': found})

    def run(self, prompt, images=(), start=None, history=None):
        """Build what prompt asks for. Returns the 'done' event.

        start is a project dict to begin from, such as what is on the
        person's canvas; the agent can describe, change or replace it.
        history is the session so far ([{'user', 'agent', 'design'}], oldest
        first), so the person can refer back to it; a new session sends none.
        """
        if history:
            prompt = with_history(prompt, history)
        if start is not None:
            self.workspace.store(start, theirs=True)
            prompt = ('The design on my canvas right now is already loaded as the current design '
                      f'({project.summary(start)}). Change it if my request is about it; '
                      'make a new one if I ask for something new.\n\n' + prompt)
        content = reference_images(self.model, images) + [{'type': 'text', 'text': prompt}]
        if len(content) > 1 and providers.provider_of(self.model).api == 'anthropic':
            # The pictures go back with every round: cached after the first, a tenth of the price.
            content[-1]['cache_control'] = {'type': 'ephemeral'}
        messages = [{'role': 'user', 'content': content}]
        said = []
        try:
            for round_ in range(1, self.max_rounds + 1):
                self.log(f'round {round_}: asking {self.model} (effort {self.effort}, {len(messages)} messages)')
                # The panel shows that the model is thinking from here until it answers.
                self.on_event({'type': 'round', 'round': round_})
                asked = time.monotonic()
                with self.log.waiting(f"{self.label}'s answer (round {round_})"):
                    response = self.call(messages)
                self.count(response)
                usage = response.usage
                parts = [b.type if b.type != 'tool_use' else f'tool_use:{b.name}' for b in response.content]
                self.log(f'round {round_}: answered in {time.monotonic() - asked:.1f}s, stop {response.stop_reason}, '
                         f'{getattr(usage, "input_tokens", 0) or 0} in + '
                         f'{getattr(usage, "cache_read_input_tokens", 0) or 0} cached / '
                         f'{getattr(usage, "output_tokens", 0) or 0} out tokens, request so far ${self.cost:.3f}; '
                         f'{", ".join(parts) or "empty"}')
                # Append the whole turn, thinking blocks included: the API
                # needs them back unchanged.
                messages.append({'role': 'assistant', 'content': response.content})
                for block in response.content:
                    if block.type == 'text' and block.text.strip():
                        said.append(block.text.strip())
                        self.on_event({'type': 'text', 'text': block.text.strip()})
                    else:
                        self.report(block)
                if response.stop_reason == 'refusal':
                    return self.finish(said, error=f'{self.label} declined this request.')
                if response.stop_reason == 'max_tokens':
                    return self.finish(said, error=f'{self.label} ran out of room for its answer.')
                if response.stop_reason == 'pause_turn':
                    continue  # a long server-side search: send the turn back to resume it
                if response.stop_reason != 'tool_use':
                    return self.finish(said)
                results = [self.tool(block) for block in response.content if block.type == 'tool_use']
                messages.append({'role': 'user', 'content': results})
                if self.cost > self.max_cost:
                    return self.finish(said, error=f'Stopped at the ${self.max_cost:.2f} limit for one request.')
            return self.finish(said, error=f'Stopped after {self.max_rounds} rounds without finishing.')
        finally:
            with self.quiet():
                self.workspace.close()

    def tool(self, block):
        args = block.input if isinstance(block.input, dict) else {}
        self.on_event({'type': 'tool_start', 'name': block.name, 'input': args})
        from .progress import Progress
        name = block.name
        self.workspace.progress = Progress(lambda event: self.on_event(dict(event, name=name)))
        self.log(f'tool {name} starts: {short(json.dumps(args), 400)}')
        began = time.monotonic()
        result = None
        try:
            with self.log.waiting(f'tool {name} to finish'):
                result = self._tool(block, args)
            return result
        finally:
            self.workspace.progress = None
            took = time.monotonic() - began
            if result is None:
                self.log(f'tool {name} crashed after {took:.1f}s')
            elif result.get('is_error'):
                self.log(f'tool {name} failed after {took:.1f}s: {short(result["content"])}')
            else:
                content = result['content']
                said = content if isinstance(content, str) else f'{len(content)} block(s)'
                self.log(f'tool {name} done in {took:.1f}s: {short(said)}')

    def _tool(self, block, args):
        from .app import APP_TOOL_NAMES, AppError
        try:
            if block.name in APP_TOOL_NAMES:
                if self.app is None:
                    raise ToolError('this tool works only when OpenStrand Studio started you')
                summary, content = self.app_tool(block.name, args)
            else:
                with self.quiet():
                    summary, content = self.workspace.run(block.name, args)
        except (ToolError, AppError, ValueError, KeyError, TypeError) as e:
            message = str(e) if not isinstance(e, KeyError) else f'missing argument {e}'
            self.on_event({'type': 'tool_end', 'name': block.name, 'ok': False, 'summary': message})
            return {'type': 'tool_result', 'tool_use_id': block.id, 'content': message, 'is_error': True}
        except Exception as e:  # a crash inside the app's code: tell the agent, keep going
            message = f'{type(e).__name__}: {e}'
            self.on_event({'type': 'tool_end', 'name': block.name, 'ok': False, 'summary': message})
            return {'type': 'tool_result', 'tool_use_id': block.id, 'content': message, 'is_error': True}
        end = {'type': 'tool_end', 'name': block.name, 'ok': True, 'summary': summary}
        image = self.tool_image(block.name, args)
        if image:
            end['image'] = image
        self.on_event(end)
        return {'type': 'tool_result', 'tool_use_id': block.id, 'content': content}

    def tool_image(self, name, args):
        """The picture for a finished tool's row, where one says something: the design it
        made, changed, checked or read (a mask edit's preview when previewed). Tools that
        answer with words (lists, descriptions, settings) get none; the app pictures the
        tools that act on its own windows itself. A picture that fails never fails the tool."""
        ws = self.workspace
        if name not in IMAGE_TOOLS or ws.data is None or self.app is None:  # only the app shows them
            return None
        try:
            with self.quiet():
                if name == 'edit_mask' and args.get('preview') and ws.last_edit is not None:
                    return str(ws.snapshot(ws.last_edit))
                if name == 'draw_steps' and ws.sheet is not None and ws.sheet[0] == ws.version:
                    return str(ws.sheet[1])  # all the steps, not only the last
                if name == 'render' and args.get('step') and (ws.out_dir / f"step_{args['step']}.png").exists():
                    return str(ws.out_dir / f"step_{args['step']}.png")  # the step it looked at
                return str(ws.snapshot())
        except Exception as e:  # noqa: BLE001
            self.log(f'no picture for {name}: {type(e).__name__}: {e}')
            return None

    def app_tool(self, name, args):
        """A tool the running app does with its own code, through the bridge (openstrand/app/)."""
        from .app import HANDLERS
        return HANDLERS[name](self, args)

    def finish(self, said, error=None):
        self.log(f'request ends: {error or "answered"} (cost ${self.cost:.3f}, {self.searches} web searches)')
        ws = self.workspace
        event = {'type': 'done', 'ok': error is None, 'error': error,
                 'text': said[-1] if said else '',
                 'project': str(ws.project_path) if ws.data is not None else None,
                 'png': str(ws.png_path) if ws.rendered_version == ws.version and ws.data is not None else None,
                 'cost': round(self.cost, 4), 'model': self.model, 'searches': self.searches,
                 'plan': self.plan, 'opened_tabs': self.opened_tabs, **self.usage,
                 # Whether the design is this request's work: False while it is still the person's
                 # own as read (their canvas, a tab or a past step of one), which is never shared.
                 'changed': ws.data is not None and not ws.theirs,
                 # Whether the design was made from nothing of the person's: False once this request
                 # read their canvas, a tab or a past step. Only such a design may go in the gallery.
                 'new': ws.data is not None and not ws.own}
        if self.plan:  # a plan builds nothing, whatever is in the workspace
            event['project'] = event['png'] = None
        if ws.tab is not None:
            # The design is the person's own tab (read, or changed in place
            # with edit_mask_in_tab): it is there already, not a new design.
            event['project'] = event['png'] = None
            event['in_tab'] = ws.tab
        self.on_event(event)
        return event


# Tools whose finished row shows the design they made, changed, checked or read.
IMAGE_TOOLS = {'load_sample', 'make_turks_head', 'make_mxn', 'make_heart', 'draw_design', 'draw_steps', 'tie_knot',
               'edit_mask', 'recolor', 'make_steps', 'render', 'identify_knot', 'check_masks', 'read_tab',
               'read_tab_step'}

HISTORY_TURNS = 8


def with_history(prompt, history):
    """The request with the session's earlier turns before it, kept short."""
    lines = ['Earlier in this conversation, oldest first (the person may refer to it):']
    for turn in history[-HISTORY_TURNS:]:
        lines.append(f"- The person asked: {str(turn.get('user', ''))[:600]}")
        if turn.get('agent'):
            lines.append(f"  You answered: {str(turn['agent'])[:900]}")
        if turn.get('design'):
            lines.append(f"  The design: {turn['design']}")
        if turn.get('tools'):
            lines.append('  Tools you ran (how each ended, its time): ' + '; '.join(map(str, turn['tools']))[:900])
    return '\n'.join(lines) + '\n\nNow the person asks:\n' + prompt


# What a terminal says for each progress stage (the app translates them itself).
STAGES = {'lay_out': 'laying the cord out', 'tighten': 'pulling the knot tight',
          'draw_step': 'drawing step {step} of {steps}', 'draw': 'fitting strands to the cords'}
_last_progress = {}


def stage_text(event):
    text = STAGES.get(event.get('stage'), event.get('stage') or 'working')
    try:
        return text.format(**event)
    except (KeyError, IndexError, ValueError):
        return text


def print_events(event, as_json=False, out=None):
    """Show agent events in a terminal: JSON lines for programs, short lines for people.
    out: where to write (default stdout)."""
    out = out or sys.stdout
    if as_json:
        print(json.dumps(event), file=out, flush=True)
        return
    print_ = lambda text: print(text, file=out, flush=True)
    kind = event['type']
    if kind == 'tool_progress':
        # One line when the stage changes or another tenth is done, not one per event.
        key = (event.get('name'), stage_text(event), int(10 * (event.get('fraction') or 0)))
        if key != _last_progress.get('key'):
            _last_progress['key'] = key
            print_(f"    {int(100 * (event.get('fraction') or 0)):3d}% {stage_text(event)}")
        return
    if kind == 'text':
        print_(f"agent: {event['text']}")
    elif kind == 'thinking':
        print_(f"  (thinking) {event['text']}")
    elif kind == 'search':
        print_(f"  … {event['name']} {event['query']}".rstrip())
    elif kind == 'search_result':
        found = f"{event['results']} results" if event['results'] is not None else 'done'
        print_(f"  {'✓' if event['ok'] else '✗'} {event['name']}: {found if event['ok'] else event['error']}")
    elif kind == 'note':
        print_(f"note: {event['text']}")
    elif kind == 'tool_start':
        args = ' '.join(f'{k}={v}' for k, v in event['input'].items())
        print_(f"  … {event['name']} {args[:200]}".rstrip())
    elif kind == 'tool_end':
        print_(f"  {'✓' if event['ok'] else '✗'} {event['summary']}")
    elif kind == 'done':
        if event['error']:
            print_(f"error: {event['error']}")
        if event['project']:
            print_(f"wrote {event['project']}")
        searches = f" · {event['searches']} web searches" if event.get('searches') else ''
        print_(f"cost ${event['cost']:.4f} · {event['model']}{searches}")
