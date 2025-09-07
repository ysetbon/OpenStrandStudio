# RTL/LTR Settings Alignment Rule for OpenStrand Studio

## Problem
When switching between Hebrew (RTL) and English (LTR) languages, all checkbox options in the settings dialog must properly reorganize their layout to match the reading direction.

## Solution Pattern
Every checkbox option in settings_dialog.py must be handled in the `reorganize_layouts_for_language` function.

## Required Implementation Steps

### 1. When Creating a New Checkbox Option

Create the layout and widgets with proper naming:
```python
# Create layout as instance attribute
if not hasattr(self, 'your_option_layout'):
    self.your_option_layout = QHBoxLayout()

# Create label and checkbox
self.your_option_label = QLabel(_['your_option_text'])
self.your_option_checkbox = QCheckBox()
self.your_option_checkbox.setChecked(self.your_option_value)

# Add widgets in proper order for current language
if self.is_rtl_language(self.current_language):
    self.your_option_layout.addStretch()
    self.your_option_layout.addWidget(self.your_option_checkbox)
    self.your_option_layout.addWidget(self.your_option_label)
else:
    self.your_option_layout.addWidget(self.your_option_label)
    self.your_option_layout.addWidget(self.your_option_checkbox)
    self.your_option_layout.addStretch()

# Add to parent layout
general_layout.addLayout(self.your_option_layout)
```

### 2. Add to reorganize_layouts_for_language Function

In the `reorganize_layouts_for_language` method (around line 554), add reorganization code:
```python
# Your option layout reorganization
if hasattr(self, 'your_option_layout') and hasattr(self, 'your_option_label') and hasattr(self, 'your_option_checkbox'):
    self.clear_layout(self.your_option_layout)
    if is_rtl:
        self.your_option_layout.addStretch()
        self.your_option_layout.addWidget(self.your_option_checkbox)
        self.your_option_layout.addWidget(self.your_option_label)
    else:
        self.your_option_layout.addWidget(self.your_option_label)
        self.your_option_layout.addWidget(self.your_option_checkbox)
        self.your_option_layout.addStretch()
    # Force immediate update
    self.your_option_layout.invalidate()
    self.your_option_layout.activate()
```

### 3. Update Text in update_texts Method

In the `update_texts` method (around line 3500), add text update:
```python
self.your_option_label.setText(_['your_option_text'] if 'your_option_text' in _ else "Your default text")
```

## Layout Direction Rules

### RTL (Hebrew, Arabic, etc.)
- Order: [Stretch] [Checkbox] [Label]
- Checkbox appears on the RIGHT
- Label appears on the LEFT
- Reading flows right-to-left

### LTR (English, French, etc.)
- Order: [Label] [Checkbox] [Stretch]
- Label appears on the LEFT
- Checkbox appears on the RIGHT
- Reading flows left-to-right

## Complete Example - Show Highlights Option

```python
# 1. In setup_ui (around line 1594):
if not hasattr(self, 'show_highlights_layout'):
    self.show_highlights_layout = QHBoxLayout()
self.show_highlights_label = QLabel(_['show_move_highlights'] if 'show_move_highlights' in _ else "Show highlights in move modes")
self.show_highlights_checkbox = QCheckBox()
self.show_highlights_checkbox.setChecked(self.show_move_highlights)

if self.is_rtl_language(self.current_language):
    self.show_highlights_layout.addStretch()
    self.show_highlights_layout.addWidget(self.show_highlights_checkbox)
    self.show_highlights_layout.addWidget(self.show_highlights_label)
else:
    self.show_highlights_layout.addWidget(self.show_highlights_label)
    self.show_highlights_layout.addWidget(self.show_highlights_checkbox)
    self.show_highlights_layout.addStretch()

general_layout.addLayout(self.show_highlights_layout)

# 2. In reorganize_layouts_for_language (around line 634):
if hasattr(self, 'show_highlights_layout') and hasattr(self, 'show_highlights_label') and hasattr(self, 'show_highlights_checkbox'):
    self.clear_layout(self.show_highlights_layout)
    if is_rtl:
        self.show_highlights_layout.addStretch()
        self.show_highlights_layout.addWidget(self.show_highlights_checkbox)
        self.show_highlights_layout.addWidget(self.show_highlights_label)
    else:
        self.show_highlights_layout.addWidget(self.show_highlights_label)
        self.show_highlights_layout.addWidget(self.show_highlights_checkbox)
        self.show_highlights_layout.addStretch()
    self.show_highlights_layout.invalidate()
    self.show_highlights_layout.activate()

# 3. In update_texts (around line 3507):
self.show_highlights_label.setText(_['show_move_highlights'] if 'show_move_highlights' in _ else "Show highlights in move modes")
```

## Testing Checklist
- [ ] Switch from English to Hebrew - checkbox moves to right
- [ ] Switch from Hebrew to English - checkbox moves to right (of the label)
- [ ] Layout updates immediately without restart
- [ ] No visual glitches or overlapping
- [ ] Stretch spacer maintains proper alignment

## Common Mistakes to Avoid
1. **Forgetting to add to reorganize_layouts_for_language** - This causes alignment to break on language switch
2. **Not using instance attributes** - Always use `self.layout_name` not local variables
3. **Missing hasattr checks** - Always check attributes exist before reorganizing
4. **Not calling invalidate/activate** - Layout won't update visually without these
5. **Wrong widget order** - Remember RTL reverses the entire order, not just alignment

## Files to Modify
- `src/settings_dialog.py` - Main settings dialog implementation
- `src/translations.py` - Add translation keys for new options

## Related Functions
- `reorganize_layouts_for_language()` - Main reorganization function (line ~554)
- `update_texts()` - Updates all text labels (line ~3493)
- `setup_ui()` - Initial UI setup (line ~1347)
- `is_rtl_language()` - Checks if language is RTL (line ~317)