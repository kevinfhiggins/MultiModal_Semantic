from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class Modality(str, Enum):
    """Data modality types"""
    PDF = "pdf"
    AUDIO = "audio"
    IMAGE = "image"
    VIDEO = "video"
    ALL = "all"


class SearchRequest(BaseModel):
    """Search request payload"""
    query: str = Field(..., min_length=1, description="Natural language search query")
    modality: Optional[Modality] = Field(Modality.ALL, description="Filter by modality")
    top_k: int = Field(10, ge=1, le=100, description="Number of results to return")


class SearchResult(BaseModel):
    """Individual search result"""
    id: str = Field(..., alias="_id")
    title: str
    modality: str
    score: Optional[float] = None
    normalized_score: Optional[float] = None  # FIX 3: Min-max normalized 0-100 confidence
    preview: str
    tags: List[str] = []
    source_file: str
    file_url: Optional[str] = None
    metadata: Dict[str, Any] = {}
    timestamp: Optional[float] = None  # For audio: playback timestamp in seconds
    matched_text: Optional[str] = None  # For audio: matched text snippet

    class Config:
        populate_by_name = True


class SearchTrailStep(BaseModel):
    """A single step in the search pipeline trail"""
    label: str
    detail: str
    icon: str = ""


class SearchResponse(BaseModel):
    """Search response with results"""
    query: str
    results: List[SearchResult]
    total: int
    modality_filter: Optional[str] = None
    search_info: Optional[str] = None  # Explanation of which embedding models were used
    search_trail: List[SearchTrailStep] = []  # Pipeline trail for transparency


class DocumentUpload(BaseModel):
    """Document upload metadata"""
    title: str
    modality: Modality
    tags: List[str] = []
    metadata: Dict[str, Any] = {}


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    mongodb_connected: bool
    voyage_configured: bool
    timestamp: str


class ConfigStatusResponse(BaseModel):
    """Configuration status response"""
    mongodb_uri_set: bool
    mongodb_database: str
    mongodb_collection: str
    voyage_api_key_set: bool
    voyage_model: str
    vector_index_name: str
    vector_dimension: int


class DocumentRecord(BaseModel):
    """Internal document record for MongoDB - stores only embeddings and metadata with file links"""
    title: str
    modality: str
    source_file: str
    file_path: str  # Path to actual file on disk
    file_url: Optional[str] = None  # URL to access the file
    preview: str
    tags: List[str] = []
    metadata: Dict[str, Any] = {}
    embedding: List[float]
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # For audio files: array of semantic chunks with individual embeddings
    audio_chunks: Optional[List[Dict[str, Any]]] = None

    # For video files: multimodal chunks (audio + visual keyframes with embeddings)
    video_chunks: Optional[List[Dict[str, Any]]] = None

    # Note: Full text_content, transcript, and image_caption are NOT stored
    # Only used during embedding generation, then discarded
