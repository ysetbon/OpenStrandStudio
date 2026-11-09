"""What every test shares."""
import os
import sys
import tempfile
from pathlib import Path

import pytest

# The tests save made-up API keys: never in this computer's real password store (macOS
# Keychain, Windows Credential Manager, the Secret Service), where they would replace the
# person's own. claude_settings keeps them in the test's own settings folder instead.
os.environ["OPENSTRAND_KEYCHAIN"] = "off"

SRC = Path(__file__).resolve().parents[1] / "src"
_spare = []  # a folder of the tests' own, for a test on macOS that sets no APPDATA


@pytest.fixture(autouse=True)
def claude_settings_never_the_real_ones(monkeypatch):
    """On macOS the app keeps claude.json in ~/Library whatever APPDATA says, so the tests,
    which give each run an APPDATA folder of its own, would read and write the person's real
    settings, their keys among them. In the tests it follows APPDATA there too, as on Windows
    and Linux, and is never the real folder."""
    if sys.platform != "darwin":
        return
    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))
    import claude_settings
    if not _spare:
        _spare.append(tempfile.mkdtemp(prefix="oss_test_settings_"))
    monkeypatch.setattr(claude_settings, "settings_directory",
                        lambda: os.path.join(os.environ.get("APPDATA") or _spare[0], "OpenStrandStudio"))
