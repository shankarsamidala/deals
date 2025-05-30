"""
Telegram client wrapper with production-optimized connection settings.
Handles session management, connection health, and fast update reception.
"""

import sys
from pathlib import Path
from typing import Optional
from telethon import TelegramClient, connection
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, AuthKeyError, FloodWaitError, NetworkMigrateError
import asyncio
import structlog

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from core.config.settings import settings

logger = structlog.get_logger(__name__)


class TelegramClientWrapper:
    """Production-ready Telegram client with optimized connection settings for fast updates"""
    
    def __init__(self) -> None:
        self._client: Optional[TelegramClient] = None
        self._is_connected: bool = False
        self._user_info: Optional[dict] = None
    
    def _create_optimized_client(self) -> TelegramClient:
        """Create TelegramClient with production-optimized settings"""
        session = StringSession(settings.telegram_session_string)
        
        return TelegramClient(
            session,
            settings.telegram_api_id,
            settings.telegram_api_hash,
            # PRODUCTION OPTIMIZATIONS for faster updates
            connection=connection.ConnectionTcpFull,  # Use full TCP connection for faster updates
            connection_retries=5,  # Reduced from default 10
            retry_delay=1,  # Reduced from default 5
            timeout=15,  # Reduced from default 30
            receive_updates=True,  # Enable real-time updates
            auto_reconnect=True,  # Auto-reconnect on connection loss
            sequential_updates=False,  # Process updates concurrently (KEY FOR SPEED!)
            flood_sleep_threshold=60,  # Wait at most 60 seconds for flood
            request_retries=5  # Reduced from default 10
        )
    
    async def connect(self) -> bool:
        """
        Connect to Telegram with production-optimized settings
        
        Returns:
            bool: True if connected successfully, False otherwise
        """
        try:
            logger.info("Connecting to Telegram (optimized mode)", api_id=settings.telegram_api_id)
            
            # Create optimized client
            self._client = self._create_optimized_client()
            
            # Disconnect first if already connected to avoid session conflicts
            if self._client.is_connected():
                await self._client.disconnect()
                logger.debug("Disconnected existing session before reconnecting")
            
            # Connect with optimized settings
            await self._client.connect()
            
            # Check if client is authorized
            if not await self._client.is_user_authorized():
                logger.error("Telegram session is invalid or expired")
                return False
            
            # Verify connection and get user info
            me = await self._client.get_me()
            self._user_info = {
                "id": me.id,
                "first_name": me.first_name,
                "last_name": me.last_name,
                "username": me.username,
                "phone": me.phone
            }
            
            self._is_connected = True
            
            # Enable syncing (catching up with missed updates)
            await self._client.catch_up()
            logger.debug("Caught up with any missed updates")
            
            logger.info(
                "Telegram connected successfully (optimized mode)",
                user_id=me.id,
                name=me.first_name,
                username=me.username,
                connection_type="ConnectionTcpFull",
                sequential_updates=False
            )
            return True
            
        except FloodWaitError as e:
            logger.error(f"Flood wait error: Need to wait {e.seconds} seconds")
            self._is_connected = False
            await asyncio.sleep(min(e.seconds, 30))  # Wait at most 30 seconds
            return False
        except NetworkMigrateError as e:
            logger.error(f"Network error while connecting: {str(e)}")
            self._is_connected = False
            return False
        except SessionPasswordNeededError:
            logger.error("Two-factor authentication required - session invalid")
            return False
        except AuthKeyError:
            logger.error("Invalid session string - authentication failed")
            return False
        except Exception as e:
            logger.error("Failed to connect to Telegram", error=str(e))
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Telegram gracefully"""
        if self._client and self._is_connected:
            logger.info("Disconnecting from Telegram")
            try:
                await self._client.disconnect()
                self._client = None
                self._is_connected = False
                self._user_info = None
                logger.info("Telegram disconnected successfully")
            except Exception as e:
                logger.error("Error during disconnect", error=str(e))
                # Force cleanup even on error
                self._client = None
                self._is_connected = False
                self._user_info = None
    
    async def health_check(self) -> dict:
        """
        Enhanced health check with connection diagnostics
        
        Returns:
            dict: Connection status and user info
        """
        if not self._is_connected or not self._client:
            return {
                "status": "disconnected",
                "connected": False,
                "error": "No active connection"
            }
        
        try:
            # Test connection by getting current user
            me = await self._client.get_me()
            
            # Additional connection diagnostics
            is_connected = self._client.is_connected()
            
            return {
                "status": "connected",
                "connected": True,
                "is_connected": is_connected,
                "user": self._user_info,
                "session_valid": True,
                "connection_type": "ConnectionTcpFull",
                "optimizations": {
                    "sequential_updates": False,
                    "auto_reconnect": True,
                    "receive_updates": True
                }
            }
            
        except FloodWaitError as e:
            logger.warning(f"Flood wait during health check: {e.seconds}s")
            return {
                "status": "rate_limited",
                "connected": True,
                "flood_wait_seconds": e.seconds
            }
        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e)
            }
    
    async def reconnect(self) -> bool:
        """
        Enhanced reconnection with retry logic and flood wait handling
        
        Returns:
            bool: True if reconnected successfully
        """
        logger.info("Attempting to reconnect to Telegram (optimized)")
        
        # Disconnect first if needed
        if self._is_connected:
            await self.disconnect()
        
        # Multiple reconnection attempts with exponential backoff
        max_attempts = 3
        base_delay = 1
        
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"Reconnection attempt {attempt}/{max_attempts}")
                
                # Attempt reconnection
                success = await self.connect()
                if success:
                    logger.info("✅ Reconnected successfully")
                    return True
                    
            except FloodWaitError as e:
                wait_time = min(e.seconds, 30)  # Cap at 30 seconds
                logger.warning(f"Flood wait during reconnect: {wait_time}s")
                await asyncio.sleep(wait_time)
                continue
                
            except Exception as e:
                logger.error(f"Reconnection attempt {attempt} failed", error=str(e))
            
            # Exponential backoff delay
            if attempt < max_attempts:
                delay = base_delay * (2 ** (attempt - 1))
                logger.info(f"Waiting {delay}s before next attempt...")
                await asyncio.sleep(delay)
        
        logger.error(f"❌ Failed to reconnect after {max_attempts} attempts")
        return False
    
    @property
    def client(self) -> Optional[TelegramClient]:
        """Get the underlying Telegram client"""
        return self._client
    
    @property
    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self._is_connected and self._client is not None
    
    @property
    def user_info(self) -> Optional[dict]:
        """Get current user information"""
        return self._user_info