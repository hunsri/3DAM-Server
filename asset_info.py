from typing_extensions import Annotated
from fastapi.params import Form
from pydantic import BaseModel
from fastapi import HTTPException

from safety_utils import SafetyUtils

class Asset_Info(BaseModel):
    package_name: str
    version: str

    @staticmethod
    def parse_asset_info(asset_info: Annotated[str, Form(...)]) -> "Asset_Info":

        # show what fields are expected in the asset_info JSON in the error message if parsing fails
        expected_fields = list(Asset_Info.model_fields.keys())

        try:
            ret = Asset_Info.model_validate_json(asset_info)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid asset_info JSON. Expected fields: {expected_fields}")

        if not SafetyUtils.check_many_names_safety(ret.package_name, ret.version):
            raise HTTPException(status_code=400, detail="Invalid package name or version in asset_info.")

        return ret