from config import CATEGORIES_PATH
from fastapi.responses import FileResponse
import re
import os
import json

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
    def _get_asset_info_path(category_name: str, asset_name: str) -> os.PathLike:
        # Validate input names to avoid directory traversal via crafted names
        name_re = re.compile(r'^[A-Za-z0-9_.-]+$')
        if not name_re.match(category_name) or not name_re.match(asset_name):
            raise ValueError("Invalid category or asset name.")

        json_path = CATEGORIES_PATH / category_name / asset_name / "asset_info.json"

        # Resolve conservatively: allow resolving even if the target doesn't exist
        resolved_json_path = json_path.resolve(strict=False)
        base_path = CATEGORIES_PATH.resolve(strict=True)

        # Ensure the resolved path is inside the categories base
        if not resolved_json_path.is_relative_to(base_path):
            raise ValueError(f"Invalid asset info for '{asset_name}' in category '{category_name}'.")

        # Existence and type checks
        if not resolved_json_path.exists() or not resolved_json_path.is_file():
            raise ValueError(f"Asset info for '{asset_name}' in category '{category_name}' does not exist.")

        # Reject symlinks
        if resolved_json_path.is_symlink():
            raise ValueError("Asset info is a symlink and is not allowed.")

        return resolved_json_path

    @staticmethod
    def get_asset_info_file(category_name: str, asset_name: str):
        resolved_json_path = AssetManager._get_asset_info_path(category_name, asset_name)
        # Return the file response with an explicit media type
        return FileResponse(resolved_json_path, media_type='application/json', filename='asset_info.json')

    @staticmethod
    def get_asset_info(category_name: str, asset_name: str) -> str:
        resolved_json_path = AssetManager._get_asset_info_path(category_name, asset_name)
        try:
            with open(resolved_json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            raise ValueError("Asset info JSON is malformed.")

    @staticmethod
    def get_asset_preview_image(category_name: str, asset_name: str) -> FileResponse:
        # Validate input names to avoid directory traversal via crafted names
        name_re = re.compile(r'^[A-Za-z0-9_.-]+$') #TODO this only allows ASCII names for now!
        if not name_re.match(category_name) or not name_re.match(asset_name):
            raise ValueError("Invalid category or asset name.")

        image_path = CATEGORIES_PATH / category_name / asset_name / "preview.png"
        # Resolve conservatively: allow resolving even if the target doesn't exist
        resolved_image_path = image_path.resolve(strict=False)
        base_path = CATEGORIES_PATH.resolve(strict=True)

        # Ensure the resolved path is inside the categories base
        if not resolved_image_path.is_relative_to(base_path):
            raise ValueError(f"Invalid preview image for asset '{asset_name}' in category '{category_name}'.")

        # Existence and type checks
        if not resolved_image_path.exists() or not resolved_image_path.is_file():
            raise ValueError(f"Preview image for asset '{asset_name}' in category '{category_name}' does not exist.")

        # Reject symlinks to avoid follow-on attacks
        if resolved_image_path.is_symlink():
            raise ValueError("Preview image is a symlink and is not allowed.")

        # Prevent serving very large files
        try:
            size = resolved_image_path.stat().st_size
        except OSError:
            raise ValueError("Unable to access preview image size.")
        if size > MAX_PREVIEW_SIZE:
            raise ValueError("Preview image is too large.")

        # Return the file response with an explicit media type
        return FileResponse(resolved_image_path, media_type="image/png", filename="preview.png")
