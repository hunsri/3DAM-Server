import json
import uuid
from category_manager import CategoryManager
from config import CATEGORIES_PATH
from safety_utils import SafetyUtils
from fastapi.responses import FileResponse, PlainTextResponse

ASSET_PACKAGE_INFO_FILENAME = "asset_package_info.json"
ASSET_ZIP_NAME = "assets.zip"

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
    
    @staticmethod
    def does_package_exist(category_name: str, package_name: str) -> bool:
        if not SafetyUtils.check_many_names_safety(category_name, package_name):
            raise ValueError("Invalid category or package name.")

        # Check based on the existence of the package directory
        package_path = CATEGORIES_PATH / category_name / package_name
        if package_path.exists() and package_path.is_dir():
            return True
        else:
            return False
    
    @staticmethod
    def does_package_version_exist(category_name: str, package_name: str, version: str) -> bool:
        if not SafetyUtils.check_many_names_safety(category_name, package_name, version):
            raise ValueError("Invalid category, package name, or version.")

        # Check based on the existence of the version directory
        version_path = CATEGORIES_PATH / category_name / package_name / "versions" / version
        if version_path.exists() and version_path.is_dir():
            return True
        else:
            return False
    
    @staticmethod
    def create_new_package_from_asset_info(category_name: str, asset_info: dict) -> str:
        if not SafetyUtils.check_name_safety(category_name):
            raise ValueError("Invalid category name.")
        
        package_name = asset_info.get("package_name")
        if package_name is None:
            raise ValueError("Package name is missing in asset info.")
        if not SafetyUtils.check_name_safety(package_name):
            raise ValueError("Invalid package name in asset info.")
        
        version = asset_info.get("version")
        if version is None:
            version = "initial_version"
        if not SafetyUtils.check_name_safety(version):
            raise ValueError("Invalid version in asset info.")
        
        # Create the package structure
        PackageManager.create_package_structure_if_category_exists(category_name, package_name, version)
        path_to_package = CATEGORIES_PATH / category_name / package_name / "versions" / version
        return str(path_to_package)

    @staticmethod
    def create_package_structure_if_category_exists(category_name: str, package_name: str, version: str) -> None:
        if not SafetyUtils.check_many_names_safety(category_name, package_name, version):
            raise ValueError("Invalid category, package name, or version.")
        
        if not CategoryManager.does_category_exist(category_name):
            raise ValueError(f"Category '{category_name}' does not exist.")
        
        # Create the package directory structure
        package_path = CATEGORIES_PATH / category_name / package_name
        version_path = package_path / "versions" / version
        version_path.mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def create_package_info_file(category_name: str, package_name: str) -> None:
        if not SafetyUtils.check_many_names_safety(category_name, package_name):
            raise ValueError("Invalid category or package name.")
        
        package_info_path = CATEGORIES_PATH / category_name / package_name / ASSET_PACKAGE_INFO_FILENAME
        if not package_info_path.exists():
            # Create a basic package info structure
            package_info = {
                "package_uuid": str(uuid.uuid4()),
                "package_name": package_name,
                "versions": []
            }
            with open(package_info_path, 'w', encoding='utf-8') as f:
                json.dump(package_info, f, indent=4)

    @staticmethod
    def add_version_to_package_info(category_name: str, package_name: str, version: str) -> None:
        if not SafetyUtils.check_many_names_safety(category_name, package_name, version):
            raise ValueError("Invalid category, package name, or version.")
        
        package_info_path = CATEGORIES_PATH / category_name / package_name / ASSET_PACKAGE_INFO_FILENAME
        if not package_info_path.exists():
            raise ValueError(f"Package info for '{package_name}' in category '{category_name}' does not exist.")
        
        try:
            with open(package_info_path, 'r+', encoding='utf-8') as file:
                package_info = json.load(file)
                versions = package_info.get("versions")
                if versions is None:
                    versions = []
                    package_info["versions"] = versions
                if version not in versions:
                    versions.append(version)
                    file.seek(0)
                    json.dump(package_info, file, indent=4)
                    file.truncate() # In case new content is shorter than old (for potential future use cases)
        except json.JSONDecodeError:
            raise ValueError("Package info JSON is malformed.")
