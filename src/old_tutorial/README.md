# Old tutorial videos

Archived copies of the four tutorial videos that shipped with OpenStrand
Studio 1.109. They were recorded on 2026-07-15 from the 1.109 build with
`automation_tests/record_tutorial_videos.py` and were replaced on 2026-09-07 by
re-recordings of the exact same four scenarios against the 1.110 `main.py`.

The app never reads this folder: the Settings > Tutorial page plays
`src/mp4/tutorial_N.mp4` on Windows and `src/mov/tutorial_N.mov` on macOS,
and the PyInstaller specs bundle only those two folders.

| File | Scenario | Recorder flag |
| --- | --- | --- |
| tutorial_1 | Setting themes and language | `--scenario settings` |
| tutorial_2 | Right-click layer panel buttons for descriptions | `--scenario buttons` |
| tutorial_3 | First strands and a mask (2_2 under 1_1) | `--scenario mask` |
| tutorial_4 | Closing a knot from two attached strands | `--scenario knot` |
