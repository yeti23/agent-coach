from mcp.server.fastmcp import FastMCP
from pubmed_client import search_pubmed
from typing import List, Dict

# Initialize the MCP server
mcp = FastMCP("pubmed-server")

@mcp.tool()
def search_papers(query: str, max_results: int = 5) -> List[Dict]:
    """
    Searches PubMed for scientific articles based on a query.
    
    :param query: The search term (e.g., 'CRISPR gene therapy').
    :param max_results: The maximum number of results to return. Defaults to 5.
    :return: A list of articles with their PMID, title, abstract, and authors.
    """
    print(f"Searching PubMed for: {query}")
    return search_pubmed(query, max_results)

if __name__ == "__main__":
    mcp.run()
