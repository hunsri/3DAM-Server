from fastapi import FastAPI, File, UploadFile, HTTPException, Response
from fastapi.websockets import WebSocket

import shutil
import os

from config import SERVERNAME, MOTD, PORT, ASSETS_DIRECTORY, MAX_CONNECTIONS, CATEGORIES, get_server_info, get_server_info_json
from asset_manager import AssetManager

# module-level manager instance
manager = AssetManager()

app = FastAPI()

@app.get("/")
async def read_main():
    return {"msg": "Hello World"}

@app.get("/info")
async def get_info():
    return get_server_info()

@app.websocket("/ws")
async def websocket(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_json({"msg": "Hello WebSocket"})

@app.get("/assets/categories/{category_name}/{asset_name}/download")
async def download_asset_http(category_name: str, asset_name: str):
    try:
        asset_path = manager.get_asset_file_path(category_name, asset_name)
        with open(asset_path, "rb") as file:
            content = file.read()
        return Response(content=content, media_type="application/octet-stream", headers={"Content-Disposition": f"attachment; filename={asset_name}.zip"})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

#TODO stream in chunks for large files
@app.websocket("/ws/assets/categories/{category_name}/{asset_name}/download")
async def download_asset(websocket: WebSocket, category_name: str, asset_name: str):
    await websocket.accept()
    try:
        asset_path = manager.get_asset_file_path(category_name, asset_name)
        with open(asset_path, "rb") as file:
            content = file.read()

        await websocket.send_bytes(content)
    except Exception as e:
        await websocket.send_text(f"Error: {str(e)}")

@app.get("/assets/categories/{category_name}/{asset_name}/asset_info_file")
async def get_asset_info_file(category_name: str, asset_name: str):
    try:
        return manager.get_asset_info_file(category_name, asset_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
@app.get("/assets/categories/{category_name}/{asset_name}/asset_info")
async def get_asset_info(category_name: str, asset_name: str):
    try:
        info = manager.get_asset_info(category_name, asset_name)
        return info
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/assets/categories/{category_name}/{asset_name}/readme")
async def get_asset_readme(category_name: str, asset_name: str):
    try:
        return manager.get_asset_readme(category_name, asset_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/assets/categories/{category_name}/{asset_name}/license")
async def get_asset_license(category_name: str, asset_name: str):
    try:
        return manager.get_asset_license(category_name, asset_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/assets/categories/{category_name}/{asset_name}/preview")
async def get_asset_preview_image(category_name: str, asset_name: str):
    try:
        return manager.get_asset_preview_image(category_name, asset_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/assets/categories/{category_name}/assets_list")
async def list_assets_in_category(category_name: str):
    try:
        assets = manager.list_assets_in_category(category_name)
        return {"category": category_name, "assets": assets}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# TODO crude WIP test implementation for uploading assets to temp directory
# + upload to specific category after validation
# + move logic to AssetManager
@app.post("/assets/categories/{category_name}/upload")
async def upload_asset(category_name: str, file: UploadFile = File(...)):
    allowed_mime = {"application/zip", "application/x-zip-compressed"}
    filename = str(file.filename or "")

    if file.content_type not in allowed_mime and not filename.lower().endswith('.zip'):
        raise HTTPException(status_code=400, detail="File type not supported. Please upload a ZIP file.")

    # Save the uploaded file inside this project's server_assets/temp for now
    project_root = os.path.dirname(__file__) # FIXME hacky way to get project root
    server_assets_dir = os.path.join(project_root, "server_assets")
    os.makedirs(server_assets_dir, exist_ok=True)
    temp_dir = os.path.join(server_assets_dir, "temp")
    os.makedirs(temp_dir, exist_ok=True)

    # Sanitize asset_name to prevent directory traversal
    safe_asset_name = os.path.basename(filename)
    if not safe_asset_name:
        raise HTTPException(status_code=400, detail="Invalid asset name")

    file_path = os.path.join(temp_dir, f"{safe_asset_name}")

    print(file_path)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {e}")
    finally:
        try:
            await file.close()
        except Exception:
            pass

    return {"status": "ok", "filename": f"{safe_asset_name}"}