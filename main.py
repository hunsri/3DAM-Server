from fastapi import FastAPI, HTTPException
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

@app.get("/assets/categories/{category_name}/assets_list")
async def list_assets_in_category(category_name: str):
    try:
        assets = manager.list_assets_in_category(category_name)
        return {"category": category_name, "assets": assets}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))