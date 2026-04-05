"""
Class for providing utility functions for managing the asset packages.
"""
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
        """
        List all package names in the given category.<br>
        Raises ValueError if the category does not exist.<br><br>
        Effectively returns the names of all subdirectories in the category directory, since each package is represented by a folder.
        """
        category_path = CATEGORIES_PATH / category_name
        if not category_path.exists() or not category_path.is_dir():
            raise ValueError(f"Category '{category_name}' does not exist.")
        
        packages: list[str] = []
        for f in category_path.iterdir():
            if f.is_dir():
                packages.append(f.name)

        return sorted(packages, key=str.casefold)

    @staticmethod
    def get_package_info(category_name: str, package_name: str) -> dict:
        """
        Retrieves the package info JSON for the specified package.<br>
        Raises ValueError if the category or package name is invalid, if the package does not exist,
        or if the package info JSON is malformed. 
        """
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
        """
        Retrieves the latest version string for the specified package.<br>
        Raises ValueError if the version information is missing or malformed.
        Returns an empty string if the package info file does not exist or cannot be read.
        """

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
        """
        Checks if a folder of the given package name exists for the specified category.<br>
        Raises ValueError if the category or package name is invalid.<br>
        Returns `True` if the directory for the given package name exists, otherwise `False`.<br><br>
        **Note:** no check for the existence of `package_info` or any `version`.
        """
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
        """
        Checks if the version directory of the given version name exists for the specified package and category.<br>
        Raises ValueError if the category, package name, or version is invalid.<br>
        Returns `True` if the directory for the given version exists, otherwise `False`.
        """
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
        """
        Creates a new package structure based on the provided asset info and returns the path to the version directory.<br>
        Raises ValueError if the category name, package name, or version in the asset info is invalid, or if the category does not exist.<br>
        The `asset_info` dict must contain at least the keys `package_name` and optionally `version`.
        If `version` is not provided, it defaults to `"initial_version"`.
        """
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
        """
        Creates the directory structure for a package version if the specified category exists.<br>
        Raises ValueError if the category name, package name, or version is invalid, or if the category does not exist.<br><br>
        **Note**: this does not create or modify the package info file, it only creates the directory structure for the version.
        """
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
        """
        Creates the package info JSON file for the specified package if it does not already exist.<br>
        Raises ValueError if the category name or package name is invalid.<br>
        The created package info file will contain a unique `package_uuid`, the `package_name`, and an empty `versions` list.
        """
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
        """
        Adds the version entry to the `package_info` file for the specified package.<br>
        Raises ValueError if the category name, package name, or version is invalid, or if the package info file does not exist.<br>
        Raises ValueError if the package info JSON is malformed.<br>
        If the version already exists in the package info, this does nothing.
        """
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
