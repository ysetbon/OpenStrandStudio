# Group panel show/hide — UX options

Mockups for letting the user hide the group panel (the "Create Group" button and
group tree) so the canvas gets more room. Open `mockup.html` in a browser; every
mock is clickable. `mockup_groups_shown.png` / `mockup_groups_hidden.png` are
static captures of the two states (`mockup.html#hidden` opens all mocks collapsed).

## Decisions so far

- Deliverable is the mockup first; the chosen option gets implemented in PyQt afterwards.
- When the group panel is hidden the **canvas gains the room**: the layer panel's
  minimum width drops from 350 to about 210 px. The outer splitter still lets the
  user drag the layer list wider.

## The options

| | Control | Canvas gain (shown / hidden) | Effort |
|---|---|---|---|
| A | Checkable **Groups** button in the main toolbar, next to **Tabs** | 0 / +140 px | small |
| B | 14 px collapse grip on the group column's edge (chevron, label + count when collapsed) | 0 / +126 px | small–medium |
| C | Group tree becomes a collapsible **Groups** section stacked under the layer list | +140 / +140 px | large |

Recommendation in the mockup: B fits the current layout best; C gives the best
result if a layout change is acceptable; A is the quickest.

## Where each option lands in the code

- Layer panel layout: `src/layer_panel.py` — the inner `QSplitter` between the
  layer list and `right_panel` (group column) is built around line 991–1046 and is
  deliberately locked (`setChildrenCollapsible(False)`, handle disabled).
  `GROUP_PANEL_FULL_WIDTH = 140`; compact-screen arithmetic in `set_compact_reduction`.
- Main window: `src/main_window.py` — toolbar buttons (≈ line 343–381), the
  `Tabs` toggle pattern (`toggle_tabs_edge`, `apply_tabs_button_style`), the outer
  splitter and `LAYER_PANEL_FULL_MIN_WIDTH = 350`, and the settings read/write
  pattern (`load_settings_from_file`, `_save_tab_edge_position`).
- Group panel widget: `src/group_layers.py` — `GroupPanel` (≈ line 735), theme colors
  in `_get_theme_colors`, Hebrew alignment in `refresh_group_alignment`.
- Strings: `src/translations.py` — add a key in all seven languages.
