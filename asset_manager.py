from config import CATEGORIES_PATH

class AssetManager:
    
    @staticmethod
    def list_assets_in_category(category_name: str) -> list[str]:
        """List all asset filenames in the given category."""
        category_path = CATEGORIES_PATH / category_name
        if not category_path.exists() or not category_path.is_dir():
            raise ValueError(f"Category '{category_name}' does not exist.")
        
        return [f.name for f in category_path.iterdir() if f.is_dir()]