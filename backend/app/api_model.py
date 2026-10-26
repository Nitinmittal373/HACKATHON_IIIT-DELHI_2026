from pydantic import BaseModel, ConfigDict


class ApiModel(BaseModel):
    """Base of every model the API returns.

    A field with a default is still always present in an answer, so the contract marks it
    required and the frontend never has to check for a missing key.
    """

    model_config = ConfigDict(json_schema_serialization_defaults_required=True)
