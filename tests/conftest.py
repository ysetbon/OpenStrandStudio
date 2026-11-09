"""What every test shares."""
import os

# The tests save made-up API keys: never in this computer's real password store (macOS
# Keychain, Windows Credential Manager, the Secret Service), where they would replace the
# person's own. claude_settings keeps them in the test's own settings folder instead.
os.environ["OPENSTRAND_KEYCHAIN"] = "off"
