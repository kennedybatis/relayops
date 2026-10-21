"""Optional read/process MCP tools; approval is deliberately not exposed."""
import os
from mcp.server.fastmcp import FastMCP
from .core import Engine
mcp = FastMCP('relayops')

@mcp.tool()
def inspect_operation() -> dict:
    """Read local demonstration state. Contains synthetic contact data."""
    engine = Engine(os.environ.get('RELAYOPS_DB', 'runtime/relayops.db'))
    try:
        return engine.snapshot()
    finally:
        engine.close()

@mcp.tool()
def qualify_commercial_lead(lead: dict) -> dict:
    """Classify a lead and stage a local approval; never send messages."""
    engine = Engine(os.environ.get('RELAYOPS_DB', 'runtime/relayops.db'))
    try:
        return engine.process(lead)
    finally:
        engine.close()

if __name__ == '__main__':
    mcp.run(transport='stdio')
