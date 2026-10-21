"""Exercise the optional MCP server through an actual stdio client session."""
import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    root = Path(__file__).resolve().parent.parent
    with tempfile.TemporaryDirectory() as directory:
        env = dict(os.environ, RELAYOPS_DB=str(Path(directory) / 'mcp.db'))
        params = StdioServerParameters(command=sys.executable, args=['-m', 'relayops.mcp_server'], cwd=str(root), env=env)
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                names = {tool.name for tool in tools.tools}
                assert names == {'inspect_operation', 'qualify_commercial_lead'}, names
                lead = json.loads((root / 'data/leads.json').read_text())[0]
                result = await session.call_tool('qualify_commercial_lead', {'lead': lead})
                assert not result.isError
                state = await session.call_tool('inspect_operation', {})
                assert not state.isError
                payload = json.loads(state.content[0].text)
                assert len(payload['runs']) == 1
                assert payload['outbox_count'] == 0
                assert payload['audit_valid']
                print('MCP stdio: initialize, list_tools, process, inspect — PASS')

asyncio.run(main())
