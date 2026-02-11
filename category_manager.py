from config import CATEGORIES_PATH
from safety_utils import SafetyUtils

class CategoryManager:

    @staticmethod
    def does_category_exist(category_name: str) -> bool:
        if not SafetyUtils.check_name_safety(category_name):
            raise ValueError("Invalid category name.")
        
        category_path = CATEGORIES_PATH / category_name
        if category_path.exists() and category_path.is_dir():
            return True
        else:
            return False