#!/usr/bin/env bash
# Record every tutorial video in every app language on a headless Linux box
# (see the docstring of record_tutorial_videos.py for the font setup) and
# publish them to src/mp4/<lang>/ and src/mov/<lang>/.
#
#   automation_tests/record_all_tutorials.sh            # all 12 x 4
#   automation_tests/record_all_tutorials.sh "he ja" "mask knot"
#
# JOBS (default 2) recordings run side by side; more makes capture slower
# and the cursor motion choppier.
cd "$(dirname "$0")/.." || exit 1
LANGS=${1:-"en fr de it es pt he ru fi sv ja zh"}
SCENARIOS=${2:-"settings buttons mask knot"}
JOBS=${JOBS:-2}
mkdir -p automation_tests/recordings/logs
for l in $LANGS; do for s in $SCENARIOS; do echo "$l $s"; done; done |
  xargs -P "$JOBS" -L 1 bash -c '
    xvfb-run -a -s "-screen 0 1920x1080x24" \
      python3 automation_tests/record_tutorial_videos.py --lang "$0" --scenario "$1" \
      > "automation_tests/recordings/logs/$0_$1.log" 2>&1
    echo "$0 $1: $(tail -n 1 automation_tests/recordings/logs/$0_$1.log)"'
