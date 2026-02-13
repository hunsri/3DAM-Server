from typing_extensions import Annotated
from fastapi.params import Form
from pydantic import BaseModel
from fastapi import HTTPException

from safety_utils import SafetyUtils
from package_manager import PackageManager

DEFAULT_VERSION = "0.0.0"
DEFAULT_EMPTY_LIST: list = []

class Asset_Info(BaseModel):
    package_name: str
    version: str = DEFAULT_VERSION
    asset_file_name: str
    authors: list[str] | None = None
    keywords: list[str] | None = None
    origin_history: list[str] | None = None

    @staticmethod
    def parse_asset_info(asset_info: Annotated[str, Form(...)]) -> "Asset_Info":

        # show what fields are expected in the asset_info JSON in the error message if parsing fails
        expected_fields = list(filter(lambda field: Asset_Info.model_fields[field].default is not DEFAULT_VERSION and Asset_Info.model_fields[field].default is not None, Asset_Info.model_fields.keys()))

        try:
            ret = Asset_Info.model_validate_json(asset_info)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid asset_info JSON. Expected fields: {expected_fields}")

        if not SafetyUtils.check_many_names_safety(ret.package_name, ret.version, ret.asset_file_name):
            raise HTTPException(status_code=400, detail="Invalid package name, asset file name, or version in asset_info.")

        if ret.authors is None:
            ret.authors = DEFAULT_EMPTY_LIST
        if ret.keywords is None:
            ret.keywords = DEFAULT_EMPTY_LIST
        if ret.origin_history is None:
            ret.origin_history = DEFAULT_EMPTY_LIST

        return ret