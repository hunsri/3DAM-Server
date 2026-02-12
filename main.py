from typing import Annotated, Any, Dict, Optional
from fastapi import Depends, FastAPI, File, Form, Request, UploadFile, HTTPException, Response
from fastapi.websockets import WebSocket

import shutil
import os

from category_manager import CategoryManager
from config import SERVERNAME, MOTD, PORT, ASSETS_DIRECTORY, MAX_CONNECTIONS, CATEGORIES, get_server_info, get_server_info_json
from asset_manager import AssetManager
from package_manager import ASSET_ZIP_NAME, PackageManager

# from pydantic import BaseModel
from asset_info import DEFAULT_VERSION, Asset_Info
from safety_utils import SafetyUtils

# module-level manager instances
manager = AssetManager()
package_manager = PackageManager()
category_manager = CategoryManager()

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

@app.get("/assets/categories/{category_name}/{package_name}/package_info")
async def get_package_info(category_name: str, package_name: str):
    try:
        info = package_manager.get_package_info(category_name, package_name)
        return info
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/assets/categories/{category_name}/{package_name}/download")
async def download_asset_http(category_name: str, package_name: str):
    try:
        asset_path = manager.get_asset_archive_location(category_name, package_name)
        with open(asset_path, "rb") as file:
            content = file.read()
        return Response(content=content, media_type="application/octet-stream", headers={"Content-Disposition": f"attachment; filename={package_name}.zip"})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/assets/categories/{category_name}/{package_name}/asset_info_file")
async def get_asset_info_file(category_name: str, package_name: str):
    try:
        return manager.get_asset_info_file(category_name, package_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
@app.get("/assets/categories/{category_name}/{package_name}/asset_info")
async def get_asset_info(category_name: str, package_name: str):
    try:
        info = manager.get_asset_info(category_name, package_name)
        return info
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/assets/categories/{category_name}/{package_name}/readme")
async def get_asset_readme(category_name: str, package_name: str):
    try:
        return manager.get_asset_readme(category_name, package_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/assets/categories/{category_name}/{package_name}/license")
async def get_asset_license(category_name: str, package_name: str):
    try:
        return manager.get_asset_license(category_name, package_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/assets/categories/{category_name}/{package_name}/preview")
async def get_asset_preview_image(category_name: str, package_name: str):
    try:
        return manager.get_asset_preview_image(category_name, package_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/assets/categories/{category_name}/package_list")
async def list_packages_in_category(category_name: str):
    try:
        packages = package_manager.list_packages_in_category(category_name)
        return {"category": category_name, "packages": packages}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/assets/categories/{category_name}/{package_name}/check_existence")
async def check_package_existence(category_name: str, package_name: str, request: Request, version: Optional[str] = None):

    version_str = request.query_params.get("version")
    try:
        package_exists = package_manager.does_package_exist(category_name, package_name)
        if version_str is None:
            return {"package_exists": package_exists}
        
        version_exists = package_manager.does_package_version_exist(category_name, package_name, version_str)   
        return {"package_exists": package_exists, "version_exists": version_exists}
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/assets/categories/{category_name}/{package_name}/preview")
async def upload_preview_image(category_name: str, package_name: str, version: str, file: UploadFile = File(...)):
    allowed_mime = {"image/png"}
    filename = str(file.filename or "")

    if file.content_type not in allowed_mime and not any(filename.lower().endswith(ext) for ext in ['.png']):
        raise HTTPException(status_code=400, detail="File type not supported. Please upload an image file (PNG).")

    if SafetyUtils.check_many_names_safety(category_name, package_name, version) is False:
        raise HTTPException(status_code=400, detail="Invalid category, package name, or version.")

    # Check if category and package exist
    if not package_manager.does_package_version_exist(category_name, package_name, version):
        raise HTTPException(status_code=404, detail=f"Package '{package_name}' with version '{version}' does not exist in category '{category_name}'.")

    # Check if a valid exisiting preview image can be found
    try:
        manager.get_asset_preview_image(category_name, package_name, version)
        raise HTTPException(status_code=400, detail=f"A preview image already exists for package '{package_name}' with version '{version}' in category '{category_name}'.")
    except ValueError:
        pass  # No existing preview image found, which is what we want for proceeding

    preview_path = manager.get_asset_index_path(category_name, package_name, version)

    try:
        manager.create_asset_preview_image(category_name, package_name, version, await file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {e}")
    finally:
        try:
            await file.close()
        except Exception:
            pass

    return {"status": "ok", "category": category_name, "package_name": package_name}

@app.post("/assets/categories/{category_name}/upload")
async def upload_asset(category_name: str, asset_info: Annotated[Asset_Info, Depends(Asset_Info.parse_asset_info)], file: UploadFile = File(...)):
    allowed_mime = {"application/zip"}
    filename = str(file.filename or "")

    if file.content_type not in allowed_mime and not filename.lower().endswith('.zip'):
        raise HTTPException(status_code=400, detail="File type not supported. Please upload a ZIP file.")

    if SafetyUtils.check_name_safety(category_name) is False:
        raise HTTPException(status_code=400, detail="Invalid category name.")

    if asset_info.version == DEFAULT_VERSION:
        # If the version is the default, we only allow the upload if the package does not already exist
        if package_manager.does_package_exist(category_name, asset_info.package_name):
            raise HTTPException(status_code=400, detail="Version field is missing in asset_info JSON. A version is required when the package already exists.")

    # We can assume asset_info has been checked for malicious content during parsing
    # Hence values can theoretically used safely as is, though safety is advised in case parsing logic changes

    # Check if category exists
    if not category_manager.does_category_exist(category_name):
        raise HTTPException(status_code=404, detail=f"Category '{category_name}' does not exist.")

    # Check if package and version don't already exist in the category
    if package_manager.does_package_version_exist(category_name, asset_info.package_name, asset_info.version):
        raise HTTPException(status_code=400, detail=f"Package '{asset_info.package_name}' with version '{asset_info.version}' already exists in category '{category_name}'.")
    
    # Create the new package structure
    try:
        new_package_path = package_manager.create_new_package_from_asset_info(category_name, asset_info.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    file_path = os.path.join(new_package_path, ASSET_ZIP_NAME)

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
    
    PackageManager.create_package_info_file(category_name, asset_info.package_name)
    PackageManager.add_version_to_package_info(category_name, asset_info.package_name, asset_info.version)

    AssetManager.save_asset_info(category_name, asset_info.package_name, asset_info.version, asset_info.model_dump())

    return {"status": "ok", "category": category_name, "package_name": asset_info.package_name, "version": asset_info.version}