"""Errors a tool reports to Claude."""


class ToolError(Exception):
    """A tool call that cannot be done; its message goes back to Claude."""
