from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

app = FastAPI()

# Mount static files from the frontend build
app.mount("/assets", StaticFiles(directory="../frontend/dist/assets"), name="assets")


# Root route serves the index.html from the Svelte build
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
    uvicorn.run(app, host="0.0.0.0", port=8000)
