"""Base classes for mirdata."""

from functools import cached_property
from typing import Any, ClassVar, Dict

from pydantic import BaseModel, ConfigDict


class BaseDataModel(BaseModel):
    """Base model for all data models."""

    model_config = ConfigDict(arbitrary_types_allowed=True)


class BaseDatasetMixin:
    """Mixin class for all dataset tracks."""

    _cached_properties: ClassVar[Dict[str, Any]] = {}

    def _initialize_cached_properties(self):
        """Initialize cached properties."""
        for name, prop in self._cached_properties.items():
            setattr(self.__class__, name, cached_property(prop))

    @classmethod
    def register_cached_property(cls, name: str, prop: Any):
        """Register a cached property.

        Args:
            name: Name of the property
            prop: Property function
        """
        cls._cached_properties[name] = prop
