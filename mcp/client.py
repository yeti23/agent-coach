import asyncio
import sys
import argparse
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description="PubMed MCP Client")
    parser.add_argument("query", nargs="?", default="CRISPR gene therapy", help="Search query for PubMed (default: 'CRISPR gene therapy')")
    parser.add_argument("--max-results", type=int, default=5, help="Max results to fetch (default: 5)")
    args = parser.parse_args()

    # Define server parameters to run server.py under the venv's python interpreter
    server_params = StdioServerParameters(
        command=".venv/bin/python",
        args=["server.py"],
    )

    print("Connecting to PubMed MCP server...")
    
    # Establish connection with the server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()

            # 1. Discover available tools
            print("\n--- Discovering Tools ---")
            tools_response = await session.list_tools()
            print("Available tools:")
            for tool in tools_response.tools:
                print(f"  - {tool.name}: {tool.description}")

            # 2. Call the search_papers tool
            print(f"\n--- Calling search_papers with query: '{args.query}' ---")
            try:
                result = await session.call_tool(
                    "search_papers", 
                    arguments={"query": args.query, "max_results": args.max_results}
                )
                
                # Check if the tool execution was successful
                if result.isError:
                    print("Error executing tool:")
                    print(result.content)
                else:
                    # Print the results nicely
                    print("\nResults:")
                    for idx, content in enumerate(result.content, 1):
                        # The content returned by FastMCP tools is usually TextContent objects
                        if hasattr(content, "text"):
                            try:
                                # FastMCP serializes dictionary/list returns as JSON strings in TextContent
                                parsed = json.loads(content.text)
                                print(json.dumps(parsed, indent=2))
                            except json.JSONDecodeError:
                                print(content.text)
                        else:
                            print(content)
            except Exception as e:
                print(f"Failed to call tool: {e}", file=sys.stderr)

if __name__ == "__main__":
    asyncio.run(main())
