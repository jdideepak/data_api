from datetime import datetime
from enum import Enum
from typing import List

from pydantic import BaseModel, Field, Json, PositiveInt


class SubmitModel(BaseModel):
    v: PositiveInt = Field(..., alias='_v', description="Version")
    timestamp: datetime = Field(..., alias='_timestamp', description="Timestamp (UNIX Epoch)")
    country: str = Field(..., description="Country Code")
    court: str = Field(..., description="Court code")
    year: int = Field(..., description="Year")
    identifier: str = Field(..., description="Decision identifier")
    text: str = Field(..., description="Content of document")
    user_key: str = Field(..., description="User key")
    meta: Json = None

    class Config:
        schema_extra = {
            'example': {
                '_v': 1,
                '_timestamp': 1239120938,
                'country': 'BE',
                'court': 'RSCE',
                'year': 2010,
                'identifier': '999.999',
                'text': 'Lorem Ipsum ...',
                'user_key': 'OIJAS-OIQWE',
                'meta': '{}',
            }}


class ReadModel(BaseModel):
    v: PositiveInt = Field(..., alias='_v', description="Version")
    timestamp: datetime = Field(..., alias='_timestamp', description="Timestamp (UNIX Epoch)")
    ecli: str = Field(..., description="Document ECLI Identifier")

    class Config:
        schema_extra = {
            'example': {
                '_v': 1,
                '_timestamp': 1239120938,
                'ecli': 'ECLI:BE:RSCE:2020:999.999',
            }
        }


class UpdateModel(BaseModel):
    v: PositiveInt = Field(..., alias='_v', description="Version")
    timestamp: datetime = Field(..., alias='_timestamp', description="Timestamp (UNIX Epoch)")
    ecli: str = Field(..., description="Document ECLI Identifier")

    class Config:
        schema_extra = {
            'example': {
                '_v': 1,
                '_timestamp': 1239120938,
                'ecli': 'ECLI:BE:RSCE:2020:999.999',
            }
        }
