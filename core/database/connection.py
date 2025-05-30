"""
Production-ready MongoDB connection management with Motor async driver.
Handles connection pooling, health checks, and error handling.
"""

import asyncio
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import structlog
import certifi
from core.config.settings import settings

logger = structlog.get_logger(__name__)


class DatabaseConnection:
    """MongoDB connection manager with health checks and error handling"""

    def __init__(self) -> None:
        self._client: Optional[AsyncIOMotorClient] = None
        self._database: Optional[AsyncIOMotorDatabase] = None
        self._is_connected: bool = False

    async def connect(self) -> bool:
        """
        Establish connection to MongoDB

        Returns:
            bool: True if connected successfully, False otherwise
        """
        try:
            logger.info("Connecting to MongoDB", uri=settings.mongodb_uri[:50])

            # Create client with connection timeout
            self._client = AsyncIOMotorClient(
                settings.mongodb_uri,
                serverSelectionTimeoutMS=settings.mongodb_connection_timeout * 1000,
                maxPoolSize=10,
                minPoolSize=1,
                maxIdleTimeMS=30000,
                connectTimeoutMS=20000,
                socketTimeoutMS=20000,
                tlsCAFile=certifi.where(),
            )

            # Test connection
            await self._client.admin.command('ping')

            # Get database
            self._database = self._client[settings.mongodb_database]
            self._is_connected = True

            logger.info(
                "MongoDB connected successfully",
                database=settings.mongodb_database,
                connection_timeout=settings.mongodb_connection_timeout
            )
            return True

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error("Failed to connect to MongoDB", error=str(e))
            self._is_connected = False
            return False
        except Exception as e:
            logger.error("Unexpected error connecting to MongoDB", error=str(e))
            self._is_connected = False
            return False

    async def disconnect(self) -> None:
        """Close MongoDB connection"""
        if self._client:
            logger.info("Disconnecting from MongoDB")
            self._client.close()
            self._client = None
            self._database = None
            self._is_connected = False
            logger.info("MongoDB disconnected")

    async def health_check(self) -> dict:
        """
        Perform comprehensive health check

        Returns:
            dict: Health status with details
        """
        if not self._is_connected or not self._client:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": "No connection established"
            }

        try:
            # Test database ping
            start_time = asyncio.get_event_loop().time()
            await self._client.admin.command('ping')
            ping_time = (asyncio.get_event_loop().time() - start_time) * 1000

            # Get server info
            server_info = await self._client.server_info()

            return {
                "status": "healthy",
                "connected": True,
                "database": settings.mongodb_database,
                "ping_ms": round(ping_time, 2),
                "server_version": server_info.get("version", "unknown"),
                "connection_count": len(self._client.nodes)
            }

        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e)
            }

    async def get_collections_info(self) -> dict:
        """
        Get information about all collections

        Returns:
            dict: Collections with document counts
        """
        if self._database is None:
            return {"error": "Database not connected"}

        try:
            collections = {}
            collection_names = await self._database.list_collection_names()

            for name in collection_names:
                collection = self._database[name]
                count = await collection.count_documents({})
                collections[name] = {"document_count": count}

            return {
                "total_collections": len(collection_names),
                "collections": collections
            }

        except Exception as e:
            logger.error("Failed to get collections info", error=str(e))
            return {"error": str(e)}

    @property
    def database(self) -> Optional[AsyncIOMotorDatabase]:
        """Get database instance"""
        return self._database

    @property
    def client(self) -> Optional[AsyncIOMotorClient]:
        """Get client instance"""
        return self._client

    @property
    def is_connected(self) -> bool:
        """Check if connected"""
        return self._is_connected


# Global database connection instance
db_connection = DatabaseConnection()