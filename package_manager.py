import json
from config import CATEGORIES_PATH
from safety_utils import SafetyUtils
from fastapi.responses import FileResponse, PlainTextResponse

ASSET_PACKAGE_INFO_FILENAME = "asset_package_info.json"

class PackageManager:

    @staticmethod
    def list_packages_in_category(category_name: str) -> list[str]:
        """List all package names in the given category."""
        category_path = CATEGORIES_PATH / category_name
        if not category_path.exists() or not category_path.is_dir():
            raise ValueError(f"Category '{category_name}' does not exist.")
        
        return [f.name for f in category_path.iterdir() if f.is_dir()]

    @staticmethod
    def get_package_info(category_name: str, package_name: str) -> dict:
        if not SafetyUtils.check_name_safety(category_name) \
            or not SafetyUtils.check_name_safety(package_name):
            raise ValueError("Invalid category or package name.")
        
        package_info_path = CATEGORIES_PATH / category_name / package_name
        resolved_package_info_path = SafetyUtils.safe_resolved_path(package_info_path, ASSET_PACKAGE_INFO_FILENAME)
        if resolved_package_info_path is None:
            raise ValueError(f"Package info for '{package_name}' in category '{category_name}' does not exist or is unsafe to access.")
        try:
            with open(resolved_package_info_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            raise ValueError("Package info JSON is malformed.")


    @staticmethod
    def latest_version(category_name: str, package_name: str) -> str:

        # Read the package_info.json file to get the version
        try:
            package_info_path = CATEGORIES_PATH / category_name / package_name / ASSET_PACKAGE_INFO_FILENAME
            with open(package_info_path, 'r', encoding='utf-8') as f:
                package_info = json.load(f)
                versions = package_info.get("versions")

                if versions is None:
                    raise ValueError("Version information is missing in package info.")
                else:
                    # get the last entry that holds the latest version
                    return versions[-1]
        except (FileNotFoundError, json.JSONDecodeError):
            return ""