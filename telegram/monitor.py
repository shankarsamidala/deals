"""
Telegram channel monitor using individual listeners per channel approach.
Optimized for fast message detection and processing.
"""

import sys
import asyncio
import re
import time
from pathlib import Path
from typing import List, Dict, Optional, Callable
from telethon import events
from telethon.tl.types import InputPeerChannel
from datetime import datetime
import structlog

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from services.listener.telegram.client import TelegramClientWrapper

logger = structlog.get_logger(__name__)


class TelegramChannelMonitor:
    """Monitor Telegram channels using individual listeners per channel (production approach)"""
    
    def __init__(self, client: TelegramClientWrapper) -> None:
        self.client = client
        self.deal_channels: List[Dict] = []
        self.channel_peers: List[InputPeerChannel] = []
        self.message_count: int = 0
        self.is_monitoring: bool = False
        self._running: bool = False
        
        # Optimized URL regex pattern
        self.url_pattern = re.compile(
            r'(https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b'
            r'[-a-zA-Z0-9()@:%_\+.~#?&//=]*)'
        )
    
    async def discover_deal_channels(self) -> List[Dict]:
        """
        Discover channels and create InputPeerChannel objects for optimization
        
        Returns:
            List[Dict]: List of deal channels with metadata
        """
        if not self.client.is_connected:
            logger.error("Cannot discover channels - Telegram not connected")
            return []
        
        try:
            logger.info("🔍 Discovering deal channels...")
            
            # Get all dialogs (chats, groups, channels)
            dialogs = await self.client.client.get_dialogs()
            
            self.deal_channels = []
            self.channel_peers = []
            deal_keywords = ['deal', 'shoffer', 'offer', 'discount', 'coupon']
            
            for dialog in dialogs:
                if not dialog.name:
                    continue
                
                # Check if dialog name contains deal keywords
                name_lower = dialog.name.lower()
                has_deal_keyword = any(keyword in name_lower for keyword in deal_keywords)
                
                # Only include channels (not groups or private chats)
                if has_deal_keyword and dialog.is_channel:
                    channel_info = {
                        'id': dialog.entity.id,
                        'name': dialog.name,
                        'username': getattr(dialog.entity, 'username', None),
                        'participants_count': getattr(dialog.entity, 'participants_count', 0),
                        'access_hash': getattr(dialog.entity, 'access_hash', None)
                    }
                    self.deal_channels.append(channel_info)
                    
                    # Create InputPeerChannel for optimized access
                    if channel_info['access_hash']:
                        peer = InputPeerChannel(
                            channel_id=channel_info['id'],
                            access_hash=channel_info['access_hash']
                        )
                        self.channel_peers.append(peer)
            
            logger.info(
                f"📱 Found {len(self.deal_channels)} deal channels",
                total_dialogs=len(dialogs),
                deal_channels_count=len(self.deal_channels),
                peers_created=len(self.channel_peers)
            )
            
            # Log each discovered channel
            for idx, channel in enumerate(self.deal_channels, 1):
                username = f"@{channel['username']}" if channel['username'] else "No username"
                logger.info(
                    f"  {idx}. {channel['name']} ({username})",
                    channel_id=channel['id'],
                    participants=channel['participants_count']
                )
            
            return self.deal_channels
            
        except Exception as e:
            logger.error("Failed to discover deal channels", error=str(e))
            return []
    
    def extract_urls(self, text: str) -> List[str]:
        """
        Extract URLs from text using optimized regex pattern
        
        Args:
            text: Message text to extract URLs from
            
        Returns:
            List of URLs found in the text
        """
        if not text:
            return []
        
        # Use optimized regex pattern
        urls = self.url_pattern.findall(text)
        return urls
    
    def attach_listener(self, peer: InputPeerChannel, channel_name: str) -> None:
        """
        Attach individual listener for a specific channel (production approach)
        
        Args:
            peer: InputPeerChannel object for the channel
            channel_name: Display name of the channel
        """
        
        @self.client.client.on(events.NewMessage(chats=peer))
        async def handle_new_message(event):
            """Handle new message for this specific channel"""
            start_time = time.time()
            
            try:
                # Increment global message counter
                self.message_count += 1
                message_num = self.message_count
                
                # Get basic message info (fast operations)
                message_text = event.raw_text or "Media message"
                message_id = event.message.id
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                # Log immediately for fast response
                logger.info(f"📨 Message #{message_num} in {channel_name} (ID: {message_id})")
                
                # Extract URLs from message text
                urls = self.extract_urls(message_text)
                
                # Check media for URLs (webpage previews)
                if event.message.media and hasattr(event.message.media, 'webpage'):
                    webpage = event.message.media.webpage
                    if hasattr(webpage, 'url') and webpage.url:
                        if webpage.url not in urls:
                            urls.append(webpage.url)
                
                # IMMEDIATE CONSOLE OUTPUT (like original simple approach)
                print(f"\n🔔 Message #{message_num}")
                print(f"📱 Channel: {channel_name}")
                print(f"⏰ Time: {timestamp}")
                
                if urls:
                    for i, url in enumerate(urls, 1):
                        print(f"🔗 URL {i}: {url}")
                    logger.info(f"🔍 Found {len(urls)} URLs in message")
                else:
                    print(f"🔗 URLs: No URLs found")
                
                print(f"💬 Text: {message_text[:100]}{'...' if len(message_text) > 100 else ''}")
                print("-" * 60)
                
                # Mark as read (non-blocking)
                try:
                    await self.client.client.send_read_acknowledge(event.chat_id)
                except Exception as read_error:
                    logger.debug(f"Failed to mark message as read: {read_error}")
                
                # Calculate processing time
                processing_time = (time.time() - start_time) * 1000
                logger.debug(f"✅ Message #{message_num} processed in {processing_time:.2f}ms")
                
            except Exception as e:
                processing_time = (time.time() - start_time) * 1000
                logger.error(
                    f"💥 Error handling message #{message_num}",
                    error=str(e),
                    channel=channel_name,
                    processing_time_ms=processing_time
                )
    
    def register_listeners(self) -> bool:
        """Register individual listeners for each channel (production approach)"""
        if not self.client.is_connected:
            logger.warning("Client is not connected. Listeners will not be registered.")
            return False
        
        if not self.channel_peers:
            logger.warning("No channel peers available for listener registration")
            return False
        
        logger.info(f"🎯 Registering individual listeners for {len(self.channel_peers)} channels...")
        
        try:
            for i, peer in enumerate(self.channel_peers):
                channel_name = self.deal_channels[i]['name'] if i < len(self.deal_channels) else f"Channel_{peer.channel_id}"
                self.attach_listener(peer, channel_name)
                logger.debug(f"Registered listener for {channel_name}")
            
            logger.info("✅ All channel listeners registered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register listeners: {e}")
            return False
    
    async def start_monitoring(self) -> bool:
        """
        Start monitoring deal channels using individual listeners
        
        Returns:
            bool: True if monitoring started successfully
        """
        if not self.client.is_connected:
            logger.error("Cannot start monitoring - Telegram not connected")
            return False
        
        # Discover channels if not already done
        if not self.deal_channels:
            await self.discover_deal_channels()
        
        if not self.deal_channels:
            logger.error("Cannot start monitoring - No deal channels found")
            return False
        
        # Register individual listeners for each channel
        if not self.register_listeners():
            logger.error("Failed to register channel listeners")
            return False
        
        # Reset counters
        self.message_count = 0
        self.is_monitoring = True
        self._running = True
        
        logger.info(
            f"🚀 Started monitoring {len(self.deal_channels)} deal channels (individual listeners)",
            channels=[ch['name'] for ch in self.deal_channels],
            start_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        # Start connection monitor in background
        asyncio.create_task(self._connection_monitor())
        
        return True
    
    async def _connection_monitor(self):
        """Monitor connection and reconnect if needed"""
        while self._running:
            try:
                if not self.client.is_connected:
                    logger.warning("📡 Connection lost, attempting reconnect...")
                    reconnected = await self.client.reconnect()
                    if reconnected:
                        logger.info("✅ Reconnected successfully")
                        # Re-register listeners after reconnection
                        if not self.register_listeners():
                            logger.error("Failed to re-register listeners after reconnect")
                    else:
                        logger.error("❌ Failed to reconnect")
                        
            except Exception as e:
                logger.error(f"Error in connection monitor: {e}")
                
            await asyncio.sleep(5)  # Check every 5 seconds
    
    async def stop_monitoring(self) -> None:
        """Stop monitoring channels"""
        if self.is_monitoring:
            self._running = False
            self.is_monitoring = False
            logger.info(
                f"🛑 Stopped monitoring - Total messages captured: {self.message_count}",
                monitoring_duration="Active session"
            )
    
    def get_monitoring_stats(self) -> Dict:
        """
        Get current monitoring statistics
        
        Returns:
            Dict: Monitoring stats and status
        """
        return {
            "is_monitoring": self.is_monitoring,
            "total_channels": len(self.deal_channels),
            "channels": [
                {
                    "name": ch['name'],
                    "username": ch['username'],
                    "id": ch['id']
                }
                for ch in self.deal_channels
            ],
            "messages_captured": self.message_count,
            "telegram_connected": self.client.is_connected,
            "listeners_registered": len(self.channel_peers)
        }