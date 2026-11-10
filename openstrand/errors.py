"""Errors a tool reports to the agent."""


class ToolError(Exception):
    """A tool call that cannot be done; its message goes back to the agent."""
