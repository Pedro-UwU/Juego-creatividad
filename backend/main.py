from web_socket import websocket_endpoint
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Import the WebSocket handler
app = FastAPI()

# Mount static files from the frontend build directory
app.mount("/assets", StaticFiles(directory="../frontend/dist/assets"), name="assets")


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_route(websocket: WebSocket):
    await websocket_endpoint(websocket)


# Root route returns the index.html from the Svelte build
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # Path to the compiled frontend
    spa_path = Path("../frontend/dist")

    # If specific file is requested and exists, return it
    if full_path and (spa_path / full_path).exists() and not (spa_path / full_path).is_dir():
        return FileResponse(spa_path / full_path)

    # Default to index.html for SPA routing
    return FileResponse(spa_path / "index.html")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server at http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
