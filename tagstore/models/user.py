"""
User-related types
"""

from typing import NewType

from .entity import EntityId

UserId = NewType('UserId', EntityId)
