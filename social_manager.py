import json
import uuid

from config import CATEGORIES_PATH
from safety_utils import SafetyUtils

from datetime import timezone
import datetime

class SocialManager:
    """
    Class for managing social interactions (favorites and comments) for packages in the asset server.
    Each package can have a corresponding `package_socials.json` file that stores its social data.
    If the file does not exist when an interaction is attempted, it will be created.
    """

    PACKAGE_SOCIALS_FILENAME = "package_socials.json"

    @staticmethod
    def init_social_json_for_package(category_name: str, package_name: str) -> str:
        """
        Initializes the `package_socials.json` file for a given package if it doesn't already exist.
        
        Raises a ValueError if the category or package name is not safe.
        
        Returns the path to the social JSON file.
        """

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
        """
        Retrieves the favorite count for a given package.
        Also checks if the requesting user has favorited the package, returning a dict with both pieces of information.

        Returns keys `favorites_count` (int) and `user_has_favorited` (bool).
        """
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
        """
        Retrieves the raw list of user UUIDs who have favorited the package.
        
        Returns a dict with key `favorites` containing the list of user UUIDs.

        If the category or package does not exist, or if the social JSON file does not exist, returns an empty list of favorites.

        **NOTE**: This method exposes user UUIDs and should be used with caution.
        It is intended for internal use, not for direct client responses.
        """
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
        """
        Adds the user's UUID to the list of favorites for the specified package.
        If the user has already favorited the package, this method does nothing.

        Raises a ValueError if the category or package name is not safe.
        Raises a ValueError if the category or package does not exist.
        """
        if not SafetyUtils.check_many_names_safety(category_name, package_name):
            raise ValueError("Invalid category or package name.")
        
        if not SafetyUtils.does_category_and_package_exist(category_name, package_name):
            raise ValueError("Category or package not found.")

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
        """
        Removes the user's UUID from the list of favorites for the specified package.

        Raises a ValueError if the category or package name is not safe.
        Raises a ValueError if the category or package does not exist.

        Returns `True` if the user was successfully removed, or `False` if the user was not in the list.
        """
        if not SafetyUtils.check_many_names_safety(category_name, package_name):
            raise ValueError("Invalid category or package name.")
        
        if not SafetyUtils.does_category_and_package_exist(category_name, package_name):
            raise ValueError("Category or package not found.")

        social_json_path = CATEGORIES_PATH / category_name / package_name / SocialManager.PACKAGE_SOCIALS_FILENAME
        if not social_json_path.exists():
            raise ValueError("Category or package not found.")
        
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
        """
        Retrieves comments for a specific package, indicating whether each comment was made by the requesting user.

        Returns a dict with key `comments`, which is a list of comment dicts. Each comment dict includes:
        - `comment_text`: The text of the comment.
        - `timestamp`: The timestamp (ISO 8601 format string) of when the comment was made.
        - `is_user_comment`: A boolean indicating whether the comment was made by the requesting user.
        """

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
        """
        Removes a comment from a package if it matches the provided message UUID and user UUID.

        Raises a ValueError if the category or package name is not safe.

        Returns `True` if the comment was successfully removed, or `False` if no matching comment was found.
        """
        
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
        """
        Retrieves the raw list of comments for a package, including user UUIDs.

        Returns a dict with key `comments` containing the list of comment dicts.
        Each comment dict includes:
        - `user_uuid`: The UUID of the user who made the comment.
        - `comment_text`: The text of the comment.
        - `timestamp`: The timestamp (ISO 8601 format string) of when the comment was made.
        
        **NOTE**: This method exposes user UUIDs and should be used with caution.
        It is intended for internal use, not for direct client responses.
        """
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
        """
        Adds a comment to the specified package from the user with the provided text.
        If the package's social JSON file does not exist, it will be created.

        Raises a ValueError if the category or package name is not safe.

        The comment entry will include a generated message UUID, the user's UUID, the comment text, and a timestamp (ISO 8601 format string).
        """
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
        """
        Creates a comment entry dict with a generated message UUID, the user's UUID, the comment text, and a timestamp (ISO 8601 format string).
        
        Returns the comment entry as a JSON string.
        """
        
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
        """
        Checks if the `package_socials.json` file exists for the specified package.
        Also checks that the category and package names are safe.

        Raises a ValueError if the category or package name is not safe.
        
        Returns `True` if the social JSON file exists, otherwise returns `False`.
        """
        if not SafetyUtils.check_many_names_safety(category_name, package_name):
            raise ValueError("Invalid category or package name.")
        
        social_json_path = CATEGORIES_PATH / category_name / package_name / SocialManager.PACKAGE_SOCIALS_FILENAME
        return social_json_path.exists()
