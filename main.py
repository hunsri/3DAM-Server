from fastapi import FastAPI, HTTPException, Response
from fastapi.websockets import WebSocket

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