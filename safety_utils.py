"""
Class for providing safety checks for file paths and names to prevent security vulnerabilities
such as path traversal and injection attacks.

Notes:
- Uses `Path.is_relative_to()`, which requires Python 3.9+.
"""

from config import CATEGORIES_PATH
from pathlib import Path
from typing import Optional
import os
import re

class SafetyUtils:

    @staticmethod
    def check_many_names_safety(*names: str) -> bool:
        """
        Combined call of `check_name_safety` for multiple names, returning True only if all names are safe.
        """
        return all(SafetyUtils.check_name_safety(name) for name in names)

    @staticmethod
    def check_name_safety(name: str) -> bool:
        """
        Checks if the provided name is safe by ensuring it only contains allowed characters and does not include path traversal patterns.
        Allowed characters: alphanumeric, underscores, hyphens, and periods.
        """
        # Allow only alphanumeric characters, underscores, hyphens, and periods
        name_re = re.compile(r'^[A-Za-z0-9_.-]+$')
        # Note: this rejects path separators ("/", "\\"). It does not explicitly
        # reject the literal sequence ".."; traversal is prevented by resolving
        # and verifying final paths in `safe_resolved_path`.
        return bool(name_re.match(name))

    @staticmethod
    def safe_resolved_path(path_to_file: Path, file_name: str) -> Optional[os.PathLike]:
        """
        Safely resolves a file path within the categories base directory.
        Returns the resolved path if it's safe, otherwise returns None.
        """

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
    def does_category_and_package_exist(category_name: str, package_name: str) -> bool:
        """
        Checks if the specified category and package exist within the categories base directory.
        Returns True if both exist, otherwise raises a ValueError with a message.
        
        **Note**: non-atomic existence checks can lead to TOCTOU races 
        callers should re-check or open resources securely when needed
        """

        # check if the category and package exist
        category_path = CATEGORIES_PATH / category_name
        if not category_path.exists() or not category_path.is_dir():
            raise ValueError(f"Category '{category_name}' does not exist.")
        package_path = category_path / package_name
        if not package_path.exists() or not package_path.is_dir():
            raise ValueError(f"Package '{package_name}' does not exist in category '{category_name}'.")
        return True

        
    