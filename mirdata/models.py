"""Pydantic models for mirdata."""

from typing import Any, Dict, List, Optional, Union

import numpy as np
from pydantic import BaseModel, ConfigDict, Field


class BaseModelWithConfig(BaseModel):
    """Base model with configuration for numpy arrays."""

    model_config = ConfigDict(arbitrary_types_allowed=True)


class TrackPaths(BaseModelWithConfig):
    """Track paths model."""

    audio: Optional[str] = None
    audio_mono: Optional[str] = None
    audio_stereo: Optional[str] = None
    beats: Optional[str] = None
    sections: Optional[str] = None
    chords: Optional[str] = None
    keys: Optional[str] = None
    melody: Optional[str] = None
    notes: Optional[str] = None
    tempo: Optional[str] = None
    pitch: Optional[str] = None
    metadata: Optional[str] = None


class TrackMetadata(BaseModelWithConfig):
    """Track metadata model."""

    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    duration: Optional[float] = None
    genre: Optional[str] = None
    year: Optional[int] = None
    mbid: Optional[str] = None
    additional: Optional[Dict[str, Any]] = None


class Track(BaseModelWithConfig):
    """Track model."""

    track_id: str
    data_home: str
    dataset_name: str
    paths: TrackPaths
    metadata: Optional[TrackMetadata] = None


class MultiTrackPaths(BaseModelWithConfig):
    """Multi-track paths model."""

    mix: Optional[str] = None
    tracks: Dict[str, TrackPaths] = Field(default_factory=dict)


class MultiTrack(BaseModelWithConfig):
    """Multi-track model."""

    mtrack_id: str
    data_home: str
    dataset_name: str
    paths: MultiTrackPaths
    metadata: Optional[TrackMetadata] = None
    tracks: Dict[str, Track] = Field(default_factory=dict)


class F0Data(BaseModelWithConfig):
    """F0 data model."""

    times: Union[List[float], np.ndarray]
    frequencies: Union[List[float], np.ndarray]
    confidence: Optional[Union[List[float], np.ndarray]] = None


class NoteData(BaseModelWithConfig):
    """Note data model."""

    intervals: List[List[float]]
    notes: List[float]
    confidence: Optional[List[float]] = None


class BeatData(BaseModelWithConfig):
    """Beat data model."""

    times: List[float]
    positions: List[float]
    confidence: Optional[List[float]] = None


class KeyData(BaseModelWithConfig):
    """Key data model."""

    intervals: List[List[float]]
    keys: List[str]
    confidence: Optional[List[float]] = None


class ChordData(BaseModelWithConfig):
    """Chord data model."""

    intervals: List[List[float]]
    chords: List[str]
    confidence: Optional[List[float]] = None


class SectionData(BaseModelWithConfig):
    """Section data model."""

    intervals: List[List[float]]
    labels: List[str]
    confidence: Optional[List[float]] = None


class EventData(BaseModelWithConfig):
    """Event data model."""

    times: List[float]
    labels: List[str]
    confidence: Optional[List[float]] = None


class MultiF0Data(BaseModelWithConfig):
    """Multi F0 data model."""

    times: List[float]
    frequencies: List[List[float]]
    confidence: Optional[List[List[float]]] = None


class LyricData(BaseModelWithConfig):
    """Lyric data model."""

    intervals: List[List[float]]
    lyrics: List[str]
    confidence: Optional[List[float]] = None
