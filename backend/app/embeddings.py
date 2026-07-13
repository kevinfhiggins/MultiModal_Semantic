import voyageai
from typing import List, Union
import logging
import base64

from .config import Settings

logger = logging.getLogger(__name__)


class VoyageEmbeddings:
    """Voyage AI embeddings client"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = voyageai.Client(api_key=settings.voyage_api_key)
        self.model = settings.voyage_model
        logger.info(f"Voyage AI client initialized with model: {self.model}")

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text string

        Args:
            text: Input text to embed

        Returns:
            List of floats representing the embedding vector
        """
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple text strings

        Args:
            texts: List of input texts to embed

        Returns:
            List of embedding vectors
        """
        try:
            result = self.client.embed(
                texts=texts,
                model=self.model,
                input_type="document"
            )
            logger.info(f"Generated embeddings for {len(texts)} texts")
            return result.embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

    def embed_query(self, query: str, use_multimodal: bool = True) -> List[float]:
        """
        Generate embedding for a search query.
        Uses multimodal model by default for cross-modal image search.
        Can fallback to text-only model for pure text search.

        Args:
            query: Search query text
            use_multimodal: If True, use voyage-multimodal-3.5 (for images),
                          if False, use voyage-3 (for PDFs/audio/video)

        Returns:
            Query embedding vector
        """
        try:
            if use_multimodal:
                # Use voyage-multimodal-3.5 for queries that should match images
                # Keep queries natural and concise - no expansion
                result = self.client.multimodal_embed(
                    inputs=[[query]],  # Natural query, no expansion
                    model="voyage-multimodal-3.5",
                    input_type="query"  # Prepends: "Represent the query for retrieving supporting documents:"
                )
                logger.info(f"Generated multimodal query embedding for: {query[:50]}...")
                return result.embeddings[0]
            else:
                # Use voyage-3 for pure text queries (PDFs, audio, video)
                result = self.client.embed(
                    texts=[query],
                    model=self.model,
                    input_type="query"
                )
                logger.info(f"Generated text query embedding for: {query[:50]}...")
                return result.embeddings[0]
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            raise

    def embed_image(self, image_path: str, caption: str = "") -> List[float]:
        """
        Generate embedding for an image using Voyage AI multimodal model

        Args:
            image_path: Path to image file
            caption: Optional text caption to combine with image

        Returns:
            Image embedding vector
        """
        try:
            # Read and encode image as base64
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')

            # Use voyage-multimodal-3 model for image embeddings
            result = self.client.multimodal_embed(
                inputs=[[image_data, caption]] if caption else [[image_data]],
                model="voyage-multimodal-3"
            )

            logger.info(f"Generated image embedding for: {image_path}")
            return result.embeddings[0]
        except Exception as e:
            logger.error(f"Error generating image embedding: {e}")
            # Fallback: use caption only if image embedding fails
            if caption:
                logger.warning("Falling back to text-only embedding from caption")
                return self.embed_text(caption)
            raise

    def embed_images(self, image_data: List[tuple]) -> List[List[float]]:
        """
        Generate embeddings for multiple images

        Args:
            image_data: List of (image_path, caption) tuples

        Returns:
            List of image embedding vectors
        """
        embeddings = []
        for img_path, caption in image_data:
            embeddings.append(self.embed_image(img_path, caption))
        return embeddings


# Global embeddings instance
voyage_embeddings: Union[VoyageEmbeddings, None] = None


def get_embeddings() -> VoyageEmbeddings:
    """Get Voyage embeddings instance"""
    global voyage_embeddings
    if voyage_embeddings is None:
        raise RuntimeError("Voyage embeddings not initialized")
    return voyage_embeddings


def init_embeddings(settings: Settings) -> VoyageEmbeddings:
    """Initialize Voyage embeddings client"""
    global voyage_embeddings
    voyage_embeddings = VoyageEmbeddings(settings)
    return voyage_embeddings
