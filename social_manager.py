import json
import uuid

from config import CATEGORIES_PATH
from safety_utils import SafetyUtils

from datetime import timezone
import datetime

class SocialManager:

    PACKAGE_SOCIALS_FILENAME = "package_socials.json"

    @staticmethod
    def init_social_json_for_package(category_name: str, package_name: str) -> str:
        if not SafetyUtils.check_many_names_safety(category_name, package_name):
            raise ValueError("Invalid category or package name.")
        
        social_json_path = CATEGORIES_PATH / category_name / package_name / SocialManager.PACKAGE_SOCIALS_FILENAME
        if not social_json_path.exists():
            # Create a basic social info structure
            social_info = {
                "package_uuid": "",
                "favorites": [], # List of user UUIDs who favorited the package
                "comments": []   # List of comments, each comment is a dict with user UUID, comment text, timestamp
            }
            with open(social_json_path, 'w', encoding='utf-8') as f:
                json.dump(social_info, f, indent=4)
        
        return str(social_json_path)

    @staticmethod
    def get_favorites_for_package(category_name: str, package_name: str, user_uuid: str) -> dict:
        dict_with_favorites = SocialManager._get_raw_favorites_for_package(category_name, package_name)
        
        # Construct a response that includes whether the user has favorited the package and the total count of favorites
        favorites_list = dict_with_favorites.get("favorites", [])
        response = {
            "favorites_count": len(favorites_list),
            "user_has_favorited": user_uuid in favorites_list
        }
        return response

    @staticmethod
    def _get_raw_favorites_for_package(category_name: str, package_name: str) -> dict:
        social_json_path = CATEGORIES_PATH / category_name / package_name / SocialManager.PACKAGE_SOCIALS_FILENAME

        if not SafetyUtils.does_category_and_package_exist(category_name, package_name):
            return {"favorites": []}
        if not social_json_path.exists():
            return {"favorites": []}
        with open(social_json_path, 'r', encoding='utf-8') as f:
            social_info = json.load(f)
        return {"favorites": social_info.get("favorites", [])}

    @staticmethod
    def add_favorite_to_package(category_name: str, package_name: str, user_uuid: str) -> None:
        if not SafetyUtils.check_many_names_safety(category_name, package_name):
            raise ValueError("Invalid category or package name.")
        
        if not SafetyUtils.does_category_and_package_exist(category_name, package_name):
            return

        social_json_path = CATEGORIES_PATH / category_name / package_name / SocialManager.PACKAGE_SOCIALS_FILENAME
        if not social_json_path.exists():
            SocialManager.init_social_json_for_package(category_name, package_name)
        
        with open(social_json_path, 'r', encoding='utf-8') as f:
            social_info = json.load(f)
        
        if user_uuid not in social_info["favorites"]:
            social_info["favorites"].append(user_uuid)
        
        with open(social_json_path, 'w', encoding='utf-8') as f:
            json.dump(social_info, f, indent=4)

    @staticmethod
    def remove_favorite_from_package(category_name: str, package_name: str, user_uuid: str) -> bool:
        if not SafetyUtils.check_many_names_safety(category_name, package_name):
            raise ValueError("Invalid category or package name.")
        
        if not SafetyUtils.does_category_and_package_exist(category_name, package_name):
            return False

        social_json_path = CATEGORIES_PATH / category_name / package_name / SocialManager.PACKAGE_SOCIALS_FILENAME
        if not social_json_path.exists():
            return False
        
        with open(social_json_path, 'r', encoding='utf-8') as f:
            social_info = json.load(f)
        
        if user_uuid in social_info["favorites"]:
            social_info["favorites"].remove(user_uuid)
        else:
            return False
        
        with open(social_json_path, 'w', encoding='utf-8') as f:
            json.dump(social_info, f, indent=4)
        
        return True

    @staticmethod
    def get_comments_for_package(category_name: str, package_name: str, user_uuid: str) -> dict:
        
        # returns a dict without exposing the user_uuid
        # replace the user_uuid with a boolean indicating if the comment was made by the requesting user
        raw_comments = SocialManager._get_raw_comments_for_package(category_name, package_name)
        comments_without_user_uuid = []
        for comment in raw_comments.get("comments", []):
            comment_copy = comment.copy()
            comment_copy["is_user_comment"] = (comment_copy.get("user_uuid") == user_uuid)
            comment_copy.pop("user_uuid", None)
            comments_without_user_uuid.append(comment_copy)

        return {"comments": comments_without_user_uuid}

    @staticmethod
    def remove_comment_from_package(category_name: str, package_name: str, user_uuid: str, message_uuid: str) -> bool:
        if not SafetyUtils.check_many_names_safety(category_name, package_name):
            raise ValueError("Invalid category or package name.")
        
        if not SafetyUtils.does_category_and_package_exist(category_name, package_name):
            return False

        social_json_path = CATEGORIES_PATH / category_name / package_name / SocialManager.PACKAGE_SOCIALS_FILENAME
        if not social_json_path.exists():
            return False
        
        with open(social_json_path, 'r', encoding='utf-8') as f:
            social_info = json.load(f)
        
        comment_to_remove = None
        for comment in social_info.get("comments", []):
            if comment.get("message_uuid") == message_uuid and comment.get("user_uuid") == user_uuid:
                comment_to_remove = comment
                break
        
        if comment_to_remove:
            social_info["comments"].remove(comment_to_remove)
            with open(social_json_path, 'w', encoding='utf-8') as f:
                json.dump(social_info, f, indent=4)
            return True
        
        return False

    @staticmethod
    def _get_raw_comments_for_package(category_name: str, package_name: str) -> dict:
        social_json_path = CATEGORIES_PATH / category_name / package_name / SocialManager.PACKAGE_SOCIALS_FILENAME

        if not SafetyUtils.does_category_and_package_exist(category_name, package_name):
            return {"comments": []}
        if not social_json_path.exists():
            return {"comments": []}
        with open(social_json_path, 'r', encoding='utf-8') as f:
            social_info = json.load(f)
        return {"comments": social_info.get("comments", [])}

    @staticmethod
    def add_comment_to_package(category_name: str, package_name: str, user_uuid: str, comment_text: str) -> None:
        if not SafetyUtils.check_many_names_safety(category_name, package_name):
            raise ValueError("Invalid category or package name.")
        
        if not SafetyUtils.does_category_and_package_exist(category_name, package_name):
            return

        #check if the social json file exists for the package
        social_json_path = CATEGORIES_PATH / category_name / package_name / SocialManager.PACKAGE_SOCIALS_FILENAME
        if not social_json_path.exists():
            # create the social json file if it doesn't exist
            SocialManager.init_social_json_for_package(category_name, package_name)
        
        with open(social_json_path, 'r', encoding='utf-8') as f:
            social_info = json.load(f)
        
        comment_entry = SocialManager.create_comment_entry(user_uuid, comment_text)
        social_info["comments"].append(json.loads(comment_entry))
        
        with open(social_json_path, 'w', encoding='utf-8') as f:
            json.dump(social_info, f, indent=4)

    @staticmethod
    def create_comment_entry(user_uuid: str, comment_text: str) -> str:
        
        # Getting the current date and time
        dt = datetime.datetime.now(timezone.utc)
        timestamp = dt.isoformat()

        comment_entry = {
            "message_uuid": str(uuid.uuid4()),
            "user_uuid": user_uuid,
            "comment_text": comment_text,
            "timestamp": timestamp,
        }
        return json.dumps(comment_entry)
    
    @staticmethod
    def does_package_have_social_json(category_name: str, package_name: str) -> bool:
        if not SafetyUtils.check_many_names_safety(category_name, package_name):
            raise ValueError("Invalid category or package name.")
        
        social_json_path = CATEGORIES_PATH / category_name / package_name / SocialManager.PACKAGE_SOCIALS_FILENAME
        return social_json_path.exists()
