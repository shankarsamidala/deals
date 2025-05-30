"""
Message processor for extracting URLs and saving to MongoDB.
Handles URL extraction, message formatting, console logging, and database storage.
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import structlog

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from core.database.connection import db_connection
from core.database.models import TelegramMessage, UrlData, TelegramChannel

logger = structlog.get_logger(__name__)


class MessageProcessor:
    """Process incoming Telegram messages, extract URLs, and save to MongoDB"""
    
    def __init__(self) -> None:
        self.processed_count: int = 0
        self.collection_name: str = "telegram_messages"
        
        # URL regex patterns (from your original code)
        self.url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        self.domain_pattern = r'(?:www\.)?(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,6}(?:/[^\s]*)?'
    
    async def ensure_collection_exists(self) -> bool:
        """
        Ensure the telegram_messages collection exists
        
        Returns:
            bool: True if collection is ready, False otherwise
        """
        if db_connection.database is None:
            logger.error("Database connection not available")
            return False
        
        try:
            # Check if collection exists
            collection_names = await db_connection.database.list_collection_names()
            
            if self.collection_name not in collection_names:
                logger.info(f"📁 Creating collection: {self.collection_name}")
                
                # Create collection with indexes
                collection = db_connection.database[self.collection_name]
                
                # Create indexes for better performance
                await collection.create_index("message_id")
                await collection.create_index("channel.channel_id")
                await collection.create_index("received_at")
                await collection.create_index("processing_status")
                
                logger.info(f"✅ Collection '{self.collection_name}' created with indexes")
            else:
                logger.debug(f"Collection '{self.collection_name}' already exists")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to ensure collection exists", error=str(e))
            return False
    
    def extract_all_urls(self, text: str, media=None) -> List[UrlData]:
        """
        Extract ALL URLs from message text and media (enhanced from original)
        
        Args:
            text: Message text content
            media: Message media object
            
        Returns:
            List[UrlData]: All URLs found with metadata
        """
        urls_found = []
        
        if not text and not media:
            return urls_found
        
        # Extract URLs from text
        if text:
            # Primary: Find all http/https URLs
            http_urls = re.findall(self.url_pattern, text)
            for url in http_urls:
                urls_found.append(UrlData(
                    url=url,
                    url_type="http",
                    domain=self._extract_domain(url)
                ))
            
            # Secondary: Find domain patterns without http (only if no http URLs found)
            if not http_urls:
                domains = re.findall(self.domain_pattern, text)
                for domain in domains:
                    formatted_url = f"https://{domain}" if not domain.startswith('http') else domain
                    urls_found.append(UrlData(
                        url=formatted_url,
                        url_type="domain",
                        domain=self._extract_domain(formatted_url)
                    ))
        
        # Extract URLs from media
        if media and hasattr(media, 'webpage'):
            webpage = media.webpage
            if hasattr(webpage, 'url') and webpage.url:
                # Check if this URL is already in our list
                if not any(url_data.url == webpage.url for url_data in urls_found):
                    urls_found.append(UrlData(
                        url=webpage.url,
                        url_type="media",
                        domain=self._extract_domain(webpage.url)
                    ))
        
        return urls_found
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return "unknown"
    
    def format_message_for_console(self, message_data: Dict) -> str:
        """
        Format message data for console output (your original format)
        
        Args:
            message_data: Processed message data
            
        Returns:
            str: Formatted message string
        """
        separator = "=" * 80
        timestamp = message_data['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
        time_only = message_data['timestamp'].strftime("%H:%M:%S")
        
        # Truncate long messages for console display
        message_text = message_data['message_text']
        if len(message_text) > 100:
            message_text = message_text[:100] + "..."
        
        formatted = f"""
{separator}
Channel: {message_data['channel_name']}
Time: {timestamp}
URL: {message_data['url']}
Message: {message_text}
{separator}
"""
        return formatted
    
    def log_message_to_console(self, message_data: Dict, urls: List[UrlData]) -> None:
        """
        Log message to console with structured format (enhanced from your original)
        
        Args:
            message_data: Processed message data
            urls: List of extracted URLs
        """
        time_only = message_data['timestamp'].strftime("%H:%M:%S")
        
        # Console logging with emojis and structure
        logger.info(f"🔔 Message #{message_data['message_count']}")
        logger.info(f"📱 Channel: {message_data['channel_name']}")
        logger.info(f"⏰ Time: {time_only}")
        
        # Log all URLs found
        if urls:
            for i, url_data in enumerate(urls, 1):
                logger.info(f"🔗 URL {i}: {url_data.url} ({url_data.url_type})")
        else:
            logger.info("🔗 URLs: No URLs found")
        
        # Truncate message for console
        message_text = message_data['message_text']
        if len(message_text) > 100:
            display_text = message_text[:100] + "..."
        else:
            display_text = message_text
            
        logger.info(f"💬 Text: {display_text}")
        logger.info("-" * 60)
    
    async def save_to_database(self, telegram_message: TelegramMessage) -> bool:
        """
        Save message to MongoDB
        
        Args:
            telegram_message: Complete message model
            
        Returns:
            bool: True if saved successfully
        """
        try:
            # Ensure collection exists
            collection_ready = await self.ensure_collection_exists()
            if not collection_ready:
                return False
            
            collection = db_connection.database[self.collection_name]
            
            # Insert message
            result = await collection.insert_one(telegram_message.dict(by_alias=True, exclude={"id"}))
            
            logger.debug(
                "💾 Message saved to database",
                message_id=telegram_message.message_id,
                channel=telegram_message.channel.channel_name,
                urls_count=len(telegram_message.urls),
                db_id=str(result.inserted_id)
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "❌ Failed to save message to database",
                error=str(e),
                message_id=telegram_message.message_id
            )
            return False
    
    async def process_message(self, message_data: Dict) -> Dict:
        """
        Main message processing function with database storage
        
        Args:
            message_data: Raw message data from monitor
            
        Returns:
            Dict: Processed message data with database status
        """
        try:
            self.processed_count += 1
            
            # Extract ALL URLs from message text and media
            urls = self.extract_all_urls(
                message_data['message_text'], 
                message_data.get('media')
            )
            
            # Create channel model
            telegram_channel = TelegramChannel(
                channel_id=message_data['channel_id'],
                channel_name=message_data['channel_name'],
                username=None,  # Will be enhanced later if needed
                participants_count=0
            )
            
            # Create complete message model
            telegram_message = TelegramMessage(
                message_id=message_data['message_id'],
                channel=telegram_channel,
                message_text=message_data['message_text'],
                has_media=message_data.get('media') is not None,
                media_type=type(message_data.get('media')).__name__ if message_data.get('media') else None,
                urls=urls,
                url_count=len(urls),
                telegram_date=message_data['timestamp'],
                received_at=datetime.utcnow(),
                processed_at=datetime.utcnow(),
                processing_status="processed",
                message_length=len(message_data['message_text'])
            )
            
            # Log to console (enhanced with multiple URLs)
            self.log_message_to_console(message_data, urls)
            
            # Save to database
            saved = await self.save_to_database(telegram_message)
            
            # Create response data
            processed_data = {
                **message_data,
                'urls': [url.dict() for url in urls],
                'url_count': len(urls),
                'processed_at': datetime.utcnow(),
                'processor_count': self.processed_count,
                'database_saved': saved,
                'database_status': 'saved' if saved else 'failed'
            }
            
            if saved:
                logger.info(
                    f"✅ Message #{self.processed_count} processed and saved",
                    urls_found=len(urls),
                    channel=message_data['channel_name']
                )
            else:
                logger.warning(
                    f"⚠️ Message #{self.processed_count} processed but not saved to DB",
                    urls_found=len(urls)
                )
            
            return processed_data
            
        except Exception as e:
            logger.error(
                "Failed to process message",
                error=str(e),
                message_id=message_data.get('message_id', 'unknown'),
                channel=message_data.get('channel_name', 'unknown')
            )
            
            # Return basic processed data even on error
            return {
                **message_data,
                'urls': [],
                'url_count': 0,
                'processed_at': datetime.utcnow(),
                'processor_count': self.processed_count,
                'database_saved': False,
                'database_status': 'error',
                'error': str(e)
            }
    
    def get_stats(self) -> Dict:
        """
        Get processor statistics
        
        Returns:
            Dict: Processing statistics
        """
        return {
            "messages_processed": self.processed_count,
            "processor_status": "active",
            "collection_name": self.collection_name,
            "database_connected": db_connection.is_connected
        }