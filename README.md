# EU AI Act Compliance Form Builder MCP Server

> [!TIP]
> **Try it now!**  
> Add a Custom Connector to Claude.ai:  
> **Name:** EU AI Act Compliance Form Builder  
> **URL:** `https://eu-ai-act-mcp-production.up.railway.app/mcp`

This custom MCP server automates the generation of EU AI Act compliance documentation (Article 53 technical documentation) for General Purpose AI models. It directly extracts metadata from a Hugging Face model card to generate a completed `.docx` compliance form, following the General-Purpose AI Code of Practice described here: https://digital-strategy.ec.europa.eu/en/policies/contents-code-gpai


> [!TIP]
> **Best Practice:**  
> When asking the AI to generate a document, provide the **full Hugging Face Model ID** (e.g., `meta-llama/Llama-3.2-1B`) instead of a generic name like "Llama". This ensures the tool fetches the correct metadata.

## Features
- **Fetch Model Cards**: Extracts metadata from Hugging Face model cards.
- **Deep Link Analysis**: Automatically follows external links (e.g., Arxiv papers, GitHub PDFs) to gather technical details not present in the main model card.
- **Source Transparency**: Explicitly lists all data sources used (Model Card, PDF Paper, etc.) in the final output.
- **Generate Compliance Docs**: Generates a downloadable `.docx` file filled with compliance data.
- **Context Awareness**: Allows defining custom context for the LLM via `context.md`.
- **Customizable**: Adjustable `questions.json` and templates.

## How It Works
1.  **Data Retrieval**: Claude pulls the model card from Hugging Face. If the card links to a "Paper", "Technical Report", or "Arxiv" PDF, the server automatically downloads and extracts that text too.
2.  **Compliance Questions**: Claude retrieves the official EU AI Act compliance questions from the MCP server.
2.  **Processing**: Claude answers the questions for the compliance form based on the model card's extracted information.
3.  **Generation**: The data is input into the `.docx` compliance form template for you to download.

## How To Use
1.  **Add Custom Connector**: (See "Try it now" tip above or Server Setup below).
2.  **Start New Chat**: Open a fresh conversation in Claude.
3.  **Ask Claude**: "Build the EU AI Act compliance form for meta-llama/Llama-3.2-1B"
4.  **Approve Tools**: You may need to approve the individual tool calls as they run.
5.  **Download**: Claude will provide a task completion message with a download link to the generated `.docx` file.

> [!IMPORTANT]
> **Disclaimer:**  
> This tool uses AI to generate compliance documentation. **You must review all outputs for accuracy** before submitting them to the EU AI Office or any regulatory body. This tool is for assistance only and does not constitute legal advice.


## Prerequisites
- Python 3.10+
- `uv` or `pip`

## Installation
```bash
# If using uv (recommended)
uv sync

# Or with pip
pip install -r requirements.txt
```

## Server Setup

### 2. Connect with Ngrok (for Claude.ai)
Open a new terminal and expose the server:
```bash
ngrok http 8000
```
Copy `server_config.json.sample` to `server_config.json` and update it with your URL:
```bash
cp server_config.json.sample server_config.json
```
```json
{
  "public_url": "https://your-ngrok-url.ngrok-free.app"
}
```

### 1. Local Claude Desktop (Stdio)
To use this server with the Claude Desktop app locally:

1.  Open your Claude Desktop config (usually `~/Library/Application Support/Claude/claude_desktop_config.json`).
2.  Add:
    ```json
    {
      "mcpServers": {
        "eu-compliance": {
          "command": "/path/to/.venv/bin/fastmcp",
          "args": ["run", "/path/to/server.py"]
        }
      }
    }
    ```


### 3. Railway Deployment (Cloud)
This project is ready for one-click deployment on Railway.

1.  **Push to GitHub**: Create a repository and push this code.
2.  **Import to Railway**: Create a new project from your GitHub repo.
3.  **Automatic Build**: Railway will detect `Procfile` and `requirements.txt`.
4.  **Configure Start Command**: 
    -   Go to **Settings** > **Deploy** > **Start Command**.
    -   Set it to: `python run_http_server.py`
    -   (This is required to enable the custom CORS fixes).
5.  **Public URL**: Go to Settings -> Networking -> Generate Domain.
6.  **Connect**: Your MCP URL will be `https://<your-domain>.up.railway.app/mcp`.
7.  **Persistence (Optional but Recommended)**:
    -   Create a **Volume** in Railway.
    -   Mount it to `/app/generated_docs`.
    -   Add an Environment Variable: `RAILWAY_VOLUME_MOUNT_PATH=/app/generated_docs`.
    -   This ensures your generated DOCX files persist across restarts.

## Troubleshooting

### "Method Not Allowed" or "Not Found" Logs
You may see logs like:
- `POST /sse 405 Method Not Allowed`
- `GET /.well-known/... 404 Not Found`

**These are normal.** Clients often probe for OAuth endpoints (which we don't use) or attempt to POST to the stream URL during retries. As long as you see `GET /sse 200 OK`, the connection is active.

### "RuntimeError: Expected ASGI message..."
If you see a `RuntimeError` regarding `http.response.start` in the console, it typically means the client disconnected abruptly (e.g., you refreshed the page or closed Claude). The server tries to write to a closed connection. This is harmless and can be ignored.

## Files
- `server.py`: Main entry point.
- `questions.json`: Definitions of all 50+ compliance questions.
- `context.md`: Add your specific instructions for the LLM here.
- `MAPPING_GUIDE.md`: List of placeholders to use in your Word templates.
- `templates/`: Place your `.dotx` templates here.
