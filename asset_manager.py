from fastapi import HTTPException
from asset_info import DEFAULT_VERSION, Asset_Info
from category_manager import CategoryManager
from config import CATEGORIES_PATH
from fastapi.responses import FileResponse, PlainTextResponse
import os
import json
from pathlib import Path
from typing import Optional
from package_manager import PackageManager
from safety_utils import SafetyUtils

# Maximum preview image size (bytes)
MAX_PREVIEW_SIZE = 5 * 1024 * 1024  # 5 MB
ASSET_INFO_FILENAME = "asset_info.json"
ARCHIVE_NAME = "assets.zip"
README_FILENAME = "readme.md"
LICENSE_FILENAME = "license.md"
PREVIEW_IMAGE_FILENAME = "preview.png"

class AssetManager:
    """
    Class that provides static methods for asset operations.
    This includes mainly helper methods for:
    - Getting the file path to the version of a package (asset index)
    - Getting the path to various contents of a package version
    - Creating and getting the preview image for a package version
    - Saving and getting the asset info JSON for a package version
    - Checking if a specific new package version can be created
    """
    
    @staticmethod
    def get_asset_index_path(category_name: str, package_name: str, version: str = "") -> str:
        """
        Get the path to the root directory (asset index) of a specific package version.
        If the version is not provided, the latest version is used. Raises ValueError if the path is invalid or does not exist.
        """
        
        version_directory_name = ""

        if not SafetyUtils.check_many_names_safety(category_name, package_name):
            raise ValueError("Invalid category or package name")

        if version:
            if not SafetyUtils.check_name_safety(version):
                raise ValueError("Invalid version name.")
            version_directory_name = version
        else:
            version_directory_name = PackageManager.latest_version(category_name, package_name)

        asset_index_path = CATEGORIES_PATH / category_name / package_name / "versions" / version_directory_name

        # Resolve conservatively (allow non-existing targets but normalize path)
        resolved_asset_index_path = asset_index_path.resolve(strict=False)
        base_path = CATEGORIES_PATH.resolve(strict=True)

        # Ensure the resolved path is inside the categories base
        if not resolved_asset_index_path.is_relative_to(base_path):
            raise ValueError(f"Invalid package path for version '{version_directory_name}' of '{package_name}' in category '{category_name}'.")

        # Existence and type checks
        if not resolved_asset_index_path.exists() or not resolved_asset_index_path.is_dir():
            raise ValueError(f"Version '{version_directory_name}' of Package '{package_name}' in category '{category_name}' does not exist.")
 
        # Reject symlinks
        if resolved_asset_index_path.is_symlink():
            raise ValueError(f"Version '{version_directory_name}' of Package '{package_name}' in category '{category_name}' is a symlink and is not allowed.")

        return str(resolved_asset_index_path)

    @staticmethod
    def get_asset_archive_location(category_name: str, package_name: str, version: str = "") -> os.PathLike:
        """
        Get the file path of the asset archive (zip file) for a specific package version.
        If the version is not provided, the latest version is used. Raises ValueError if the path is invalid or does not exist.
        """

        resolved_asset_index_path = AssetManager.get_asset_index_path(category_name, package_name, version)
        return Path(resolved_asset_index_path) / ARCHIVE_NAME

    @staticmethod
    def _get_asset_info_path(category_name: str, package_name: str, version: str = "") -> Optional[os.PathLike]:
        """
        Get the file path of the asset info JSON for a specific package version.
        """

        resolved_asset_index_path = AssetManager.get_asset_index_path(category_name, package_name, version)
        return Path(resolved_asset_index_path) / ASSET_INFO_FILENAME

    @staticmethod
    def get_asset_info_file(category_name: str, package_name: str, version: str = "") -> FileResponse:
        """
        Get the asset info JSON file for a specific package version as a FileResponse.
        """

        resolved_json_path = AssetManager._get_asset_info_path(category_name, package_name, version)
        if resolved_json_path is None:
            raise ValueError(f"Asset info for '{package_name}' in category '{category_name}' does not exist or is unsafe to access")
        # Return the file response with an explicit media type
        return FileResponse(resolved_json_path, media_type='application/json', filename=ASSET_INFO_FILENAME)

    @staticmethod
    def get_asset_info(category_name: str, package_name: str, version: str = "") -> dict:
        """
        Get the asset info JSON content for a specific package version as a dictionary.
        If the asset info file does not exist, or if it is malformed, a ValueError is raised.
        """
        
        resolved_json_path = AssetManager._get_asset_info_path(category_name, package_name, version)
        
        if resolved_json_path is None:
            raise ValueError(f"Asset info for '{package_name}' in category '{category_name}' does not exist or is unsafe to access.")
        try:
            with open(resolved_json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            raise ValueError("Asset info JSON is malformed.")

    @staticmethod
    def get_asset_readme(category_name: str, package_name: str, version: str = "") -> PlainTextResponse:
        """
        Get the README file content for a specific package version.
        The README file is optional, so if it does not exist, a ValueError is raised.
        """

        resolved_readme_path = AssetManager.get_asset_index_path(category_name, package_name, version) + "/" + README_FILENAME
        
        if resolved_readme_path is None:
            raise ValueError(f"README for asset '{package_name}' in category '{category_name}' does not exist or is unsafe to access.")
        try:
            resolved_readme_path = Path(resolved_readme_path)
            content = resolved_readme_path.read_text(encoding='utf-8')
            return PlainTextResponse(content, media_type='text/markdown')
        except OSError:
            raise ValueError("Unable to read README file.")

    @staticmethod
    def get_asset_license(category_name: str, package_name: str, version: str = "") -> PlainTextResponse:
        """
        Get the license file content for a specific package version.
        The license file is optional, so if it does not exist, a ValueError is raised.
        """
        resolved_license_path = AssetManager.get_asset_index_path(category_name, package_name, version) + "/" + LICENSE_FILENAME
        if resolved_license_path is None:
            raise ValueError(f"License for asset '{package_name}' in category '{category_name}' does not exist or is unsafe to access.")
        try:
            resolved_license_path = Path(resolved_license_path)
            content = resolved_license_path.read_text(encoding='utf-8')
            return PlainTextResponse(content, media_type='text/plain')
        except OSError:
            raise ValueError("Unable to read license file.")

    @staticmethod
    def create_asset_preview_image(category_name: str, package_name: str, version: str, image_content: bytes):
        """
        Sets the preview image for a specific package version.
        The format is epected to be PNG and provided as raw bytes.\n
        If the image content is larger than the maximum allowed size `MAX_PREVIEW_SIZE`, or if there is an error saving the image, a ValueError is raised.
        """

        if len(image_content) > MAX_PREVIEW_SIZE:
            raise ValueError("Preview image content is too large.")
        
        resolved_image_path = AssetManager.get_asset_index_path(category_name, package_name, version) + "/" + PREVIEW_IMAGE_FILENAME
        try:
            with open(resolved_image_path, 'wb') as file:
                file.write(image_content)
        except OSError:
            raise ValueError("Unable to save preview image.")
        
    @staticmethod
    def get_asset_preview_image(category_name: str, package_name: str, version: str = "") -> FileResponse:
        """
        Get the preview image for a specific package version as a FileResponse.
        If the version is not provided, the latest version is used.\n
        If the preview image does not exist, is larger than the maximum allowed size `MAX_PREVIEW_SIZE`, or if there is an error accessing the image, a ValueError is raised.
        """
        resolved_image_path = AssetManager.get_asset_index_path(category_name, package_name, version) + "/" + PREVIEW_IMAGE_FILENAME
        
        # Prevent serving very large files
        if resolved_image_path is None:
            raise ValueError(f"Preview image for asset '{package_name}' in category '{category_name}' does not exist or is unsafe to access.")
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
    
    @staticmethod
    def save_asset_info(category_name: str, package_name: str, version: str, asset_info: dict):
        """
        Save the asset_info JSON for a specific package version.
        """

        resolved_asset_index_path = AssetManager.get_asset_index_path(category_name, package_name, version)
        asset_info_path = Path(resolved_asset_index_path) / ASSET_INFO_FILENAME
        try:
            with open(asset_info_path, 'w', encoding='utf-8') as f:
                json.dump(asset_info, f, indent=4)
        except OSError:
            raise ValueError("Unable to save asset info.")
    
    @staticmethod
    def can_upload_asset(asset_info: "Asset_Info", category_name: str) -> bool:
        """
        Checks whether a package version can be created with the given asset_info in the specified category. This includes checks for:
        - If no version was provided, if the package already exists (in which case a version is required)
        - Existence of the specified category (has to exist to upload)
        - If the package version already exists in the category (in which case the upload is rejected)
        
        If all checks pass, the method returns `True`. If any check fails, an HTTPException with an appropriate status code and message is raised.
        """

        if asset_info.version == DEFAULT_VERSION:
        # If the version is the default, we only allow the upload if the package does not already exist
            if PackageManager.does_package_exist(category_name, asset_info.package_name):
                raise HTTPException(status_code=400, detail="Version field is missing in asset_info JSON. " \
                "A version is required when the package already exists.")
        
        # Check if category exists
        if not CategoryManager.does_category_exist(category_name):
            raise HTTPException(status_code=404, detail=f"Category '{category_name}' does not exist.")

        # Check if package and version don't already exist in the category
        if PackageManager.does_package_version_exist(category_name, asset_info.package_name, asset_info.version):
            raise HTTPException(status_code=400, detail=f"Package '{asset_info.package_name}' with version '{asset_info.version}' already exists in category '{category_name}'.")

        return True
