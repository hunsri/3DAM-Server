from config import CATEGORIES_PATH
from pathlib import Path
from typing import Optional
import os
import re

class SafetyUtils:

    @staticmethod
    def check_many_names_safety(*names: str) -> bool:
        return all(SafetyUtils.check_name_safety(name) for name in names)

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