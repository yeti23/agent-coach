# PubMed Model Context Protocol (MCP) Server

This repository contains a Model Context Protocol (MCP) server that connects to the PubMed database to search and retrieve biomedical literature. It also includes clients and configurations for programmatic and command-line interaction.

This server/client MCP should be depoyed separately.

## Project Structure

- `server.py`: The MCP server built with `FastMCP`, exposing the `search_papers` tool.
- `pubmed_client.py`: A helper client that interfaces with NCBI's E-utilities via Biopython (`Bio.Entrez` and `Bio.Medline`) to query PubMed.
- `client.py`: A Python script that acts as an MCP client using standard `stdio` transport to query the server and print results.
- `.cmcp/mcp.json`: Configuration file for the `cmcp` CLI utility, allowing you to use `cmcp` like `curl` for this MCP server.
- `requirements.txt`: Specifies the Python dependencies for the project.

---

## Installation & Setup

Ensure you have **Python 3.10+** installed on your system.

1. **Create a Virtual Environment:**
   ```bash
   python3 -m venv .venv
   ```

2. **Install Dependencies:**
   Since macOS homebrew environments are often externally managed, install the required packages inside your virtual environment. If using Python 3.14+, pass the `--ignore-requires-python` flag to install the `cmcp` dependency:
   ```bash
   .venv/bin/pip install -r requirements.txt --ignore-requires-python
   ```

---

## Usage

### 1. Programmatic Python Client (`client.py`)
Run the custom Python client to query the MCP server. It connects to the server via standard I/O (stdio) transport, discovers the registered tools, and executes a search:

```bash
.venv/bin/python client.py "CRISPR gene therapy" --max-results 2
```

### 2. Command-Line Client (`cmcp`)
Use `cmcp` (the "curl for MCP servers") with the local configuration file:

- **List Available Tools:**
  ```bash
  .venv/bin/cmcp :pubmed-server tools/list
  ```

- **Execute a Search Tool:**
  Note the use of the `:=` operator to specify JSON-encoded parameters:
  ```bash
  .venv/bin/cmcp :pubmed-server tools/call name=search_papers arguments:='{"query": "mitochondria", "max_results": 1}'
  ```

---

## Technical Details

- **Email Registration**: The database queries are sent to NCBI's E-utilities. Per NCBI guidelines, queries include an email identifier configured in `pubmed_client.py`.
- **E-fetch Parsing**: Fetches results in Medline flat-file format and parses them using the robust `Bio.Medline.parse` iterator.
