## Overview

This project provides a local MCP server implementation that can be inspected and tested using the MCP Inspector tool. The inspector allows you to interact with your server, test tools, view resources, and debug the protocol implementation in real-time.

## Prerequisites

- Python 3.13 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

## Installation

### Option 1: Using uv (Recommended)

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv add -r requirements.txt
```

### Option 2: Using pip

```bash
# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running the MCP Inspector

### Start Your Dev Server

First, start your MCP server:

```bash
python main.py
```

The server should be running and ready to accept connections.

### Launch MCP Inspector


```bash
mcp dev main.py
```

#### Step 3: Access the Inspector UI

The inspector will automatically open in your default browser.

## Troubleshooting

### Inspector won't connect

- Ensure `main.py` is running without errors
- Check that the server is using stdio transport
- Verify no other process is using the inspector port

### Tool execution fails

- Check the Console tab for error messages
- Verify tool parameters match the schema
- Ensure required dependencies are installed

### Server crashes on start

- Check Python version compatibility
- Verify all dependencies in `requirements.txt` are installed
- Review error output in the terminal
