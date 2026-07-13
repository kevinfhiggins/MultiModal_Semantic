from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from typing import Optional
import logging

from .config import Settings

logger = logging.getLogger(__name__)


class MongoDB:
    """MongoDB connection manager"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client: Optional[MongoClient] = None
        self._connected = False

    def connect(self):
        """Establish MongoDB connection"""
        try:
            self.client = MongoClient(
                self.settings.mongodb_uri,
                serverSelectionTimeoutMS=5000
            )
            # Verify connection
            self.client.admin.command('ping')
            self._connected = True
            logger.info("MongoDB connection established")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"MongoDB connection failed: {e}")
            self._connected = False
            raise

    def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            self._connected = False
            logger.info("MongoDB connection closed")

    def is_connected(self) -> bool:
        """Check if MongoDB is connected"""
        return self._connected

    @property
    def database(self):
        """Get database instance"""
        if not self.client:
            raise RuntimeError("MongoDB client not initialized")
        return self.client[self.settings.mongodb_database]

    @property
    def collection(self):
        """Get MoD_Data collection"""
        return self.database[self.settings.mongodb_collection]

    def create_vector_index(self):
        """
        Create vector search index on MongoDB Atlas.

        Note: This operation must be performed via MongoDB Atlas UI or Atlas CLI.
        The index definition should be:

        {
          "fields": [
            {
              "type": "vector",
              "path": "embedding",
              "numDimensions": 1024,
              "similarity": "cosine"
            }
          ]
        }
        """
        logger.info(
            f"Vector index '{self.settings.vector_index_name}' must be created "
            "manually in MongoDB Atlas. See README.md for instructions."
        )


# Global MongoDB instance
mongodb: Optional[MongoDB] = None


def get_database() -> MongoDB:
    """Get MongoDB instance"""
    global mongodb
    if mongodb is None:
        raise RuntimeError("MongoDB not initialized. Call init_database() first.")
    return mongodb


def init_database(settings: Settings) -> MongoDB:
    """Initialize MongoDB connection"""
    global mongodb
    mongodb = MongoDB(settings)
    mongodb.connect()
    return mongodb


def close_database():
    """Close MongoDB connection"""
    global mongodb
    if mongodb:
        mongodb.disconnect()
        mongodb = None
