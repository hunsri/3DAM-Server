from config import CATEGORIES_PATH
from safety_utils import SafetyUtils

class CategoryManager:
    """
    Class for providing utility functions for managing the asset categories.
    """

    @staticmethod
    def does_category_exist(category_name: str) -> bool:
        """
        Checks if a folder of the given name exists in the categories directory.<br>
        Raises ValueError if the category name is invalid.
        """
        if not SafetyUtils.check_name_safety(category_name):
            raise ValueError("Invalid category name.")
        
        category_path = CATEGORIES_PATH / category_name
        if category_path.exists() and category_path.is_dir():
            return True
        else:
            return False