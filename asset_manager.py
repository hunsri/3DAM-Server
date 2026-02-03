from config import CATEGORIES_PATH
from fastapi.responses import FileResponse
import re
import os
import json
from pathlib import Path
from typing import Optional

# Maximum preview image size (bytes)
MAX_PREVIEW_SIZE = 5 * 1024 * 1024  # 5 MB

class AssetManager:
    
    @staticmethod
    def list_assets_in_category(category_name: str) -> list[str]:
        """List all asset filenames in the given category."""
        category_path = CATEGORIES_PATH / category_name
        if not category_path.exists() or not category_path.is_dir():
            raise ValueError(f"Category '{category_name}' does not exist.")
        
        return [f.name for f in category_path.iterdir() if f.is_dir()]
    
    @staticmethod
    def get_asset_file_path(category_name: str, asset_name: str) -> os.PathLike:

        archive_name = asset_name + ".zip"
        asset_path = CATEGORIES_PATH / category_name / asset_name / archive_name
        
        # Resolve conservatively (allow non-existing targets but normalize path)
        resolved_asset_path = asset_path.resolve(strict=False)
        base_path = CATEGORIES_PATH.resolve(strict=True)

        # Ensure the resolved path is inside the categories base
        if not resolved_asset_path.is_relative_to(base_path):
            raise ValueError(f"Invalid asset path for '{asset_name}' in category '{category_name}'.")

        # Existence and type checks
        if not resolved_asset_path.exists() or not resolved_asset_path.is_file():
            raise ValueError(f"Asset '{asset_name}' in category '{category_name}' does not exist.")

        # Reject symlinks
        if resolved_asset_path.is_symlink():
            raise ValueError("Asset archive is a symlink and is not allowed.")
        
        return resolved_asset_path

    @staticmethod
    def _get_asset_info_path(category_name: str, asset_name: str) -> Optional[os.PathLike]:
        # Validate input names to avoid directory traversal via crafted names
        if not AssetManager.check_name_safety(category_name) \
            or not AssetManager.check_name_safety(asset_name):
            raise ValueError("Invalid category or asset name.")

        json_path = CATEGORIES_PATH / category_name / asset_name / "asset_info.json"

        # Use helper to safely resolve and validate the target file; returns None on failure
        return AssetManager.safe_resolved_path(json_path.parent, "asset_info.json")

    @staticmethod
    def check_name_safety(name: str) -> bool:
        # Allow only alphanumeric characters, underscores, hyphens, and periods
        name_re = re.compile(r'^[A-Za-z0-9_.-]+$')
        return bool(name_re.match(name))

    @staticmethod
    def safe_resolved_path(path_to_file: Path, file_name: str) -> Optional[os.PathLike]:
        # Normalize to Path to access file methods safely
        path = path_to_file / file_name

        # Resolve conservatively: allow resolving even if the target doesn't exist
        resolved_file_path = path.resolve(strict=False)
        base_path = CATEGORIES_PATH.resolve(strict=True)

        # Ensure the resolved path is inside the categories base
        if not resolved_file_path.is_relative_to(base_path):
            return None
        
        # Existence and type checks
        if not resolved_file_path.exists() or not resolved_file_path.is_file():
            return None

        # Reject symlinks
        if resolved_file_path.is_symlink():
            return None
        
        return resolved_file_path

    @staticmethod
    def get_asset_info_file(category_name: str, asset_name: str):
        resolved_json_path = AssetManager._get_asset_info_path(category_name, asset_name)
        if resolved_json_path is None:
            raise ValueError(f"Asset info for '{asset_name}' in category '{category_name}' does not exist or is unsafe to access")
        # Return the file response with an explicit media type
        return FileResponse(resolved_json_path, media_type='application/json', filename='asset_info.json')

    @staticmethod
    def get_asset_info(category_name: str, asset_name: str) -> str:
        resolved_json_path = AssetManager._get_asset_info_path(category_name, asset_name)
        if resolved_json_path is None:
            raise ValueError(f"Asset info for '{asset_name}' in category '{category_name}' does not exist or is unsafe to access.")
        try:
            with open(resolved_json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            raise ValueError("Asset info JSON is malformed.")

    @staticmethod
    def get_asset_preview_image(category_name: str, asset_name: str) -> FileResponse:
        # Validate input names to avoid directory traversal via crafted names
        if not AssetManager.check_name_safety(category_name) \
            or not AssetManager.check_name_safety(asset_name):
            raise ValueError("Invalid category or asset name.")
        
        resolved_image_path = AssetManager.safe_resolved_path(CATEGORIES_PATH / category_name / asset_name, "preview.png")  

        # Prevent serving very large files
        if resolved_image_path is None:
            raise ValueError(f"Preview image for asset '{asset_name}' in category '{category_name}' does not exist or is unsafe to access.")
        else:
            resolved_image_path = Path(resolved_image_path)

        try:
            size = resolved_image_path.stat().st_size
        except OSError:
            raise ValueError("Unable to access preview image size.")
        if size > MAX_PREVIEW_SIZE:
            raise ValueError("Preview image is too large.")

        # Return the file response with an explicit media type
        return FileResponse(resolved_image_path, media_type="image/png", filename="preview.png")
