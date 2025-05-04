"""Base classes for mirdata."""
from typing import Dict, List, Optional, Any, ClassVar, Type
from typing_extensions import Annotated
import numpy as np
from pydantic import BaseModel, Field, ConfigDict
from functools import cached_property


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