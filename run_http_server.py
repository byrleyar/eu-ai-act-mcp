import uvicorn
import os
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Route
from server import mcp

# 1. Get the Streamable HTTP app
app = mcp.streamable_http_app()

# FIX: FastMCP v0.5.0 bug - The /mcp route defaults to GET-only.
# We must manually patch it to allow POST (required for JSON-RPC).
new_routes = []
for route in app.routes:
    if getattr(route, "path", "") == "/mcp":
        # Re-create the route with POST support
        print(f"Patching {route.path} to allow GET & POST")
        new_routes.append(Route("/mcp", endpoint=route.endpoint, methods=["GET", "POST"]))
    else:
        new_routes.append(route)

app.router.routes = new_routes

# 2. Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting EU AI Act Compliance Server (Streamable HTTP) on port {port}...")
    print("Endpoint: /mcp (Use this path in your URL)")
    uvicorn.run(app, host="0.0.0.0", port=port)

