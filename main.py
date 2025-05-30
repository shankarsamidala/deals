"""
Telegram Listener Service - Simplified for maximum speed.
Focuses purely on fast message detection without database overhead.
"""

import sys
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
import structlog

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.config.settings import settings
from services.listener.telegram.client import TelegramClientWrapper
from services.listener.telegram.monitor import TelegramChannelMonitor

logger = structlog.get_logger(__name__)


class TelegramListenerService:
    """Simplified service class focused on fast message monitoring"""
    
    def __init__(self) -> None:
        self.client = TelegramClientWrapper()
        self.monitor = TelegramChannelMonitor(self.client)
        self.is_running = False
    
    async def start_service(self) -> bool:
        """
        Start the simplified listener service (no database overhead)
        
        Returns:
            bool: True if service started successfully
        """
        try:
            logger.info("🚀 Starting Telegram Listener Service (Fast Mode)")
            
            # Step 1: Connect to Telegram with optimized settings
            logger.info("📡 Connecting to Telegram (optimized)...")
            connected = await self.client.connect()
            if not connected:
                logger.error("❌ Failed to connect to Telegram")
                return False
            
            # Step 2: Discover deal channels and create InputPeerChannel objects
            logger.info("🔍 Discovering deal channels...")
            channels = await self.monitor.discover_deal_channels()
            if not channels:
                logger.error("❌ No deal channels found to monitor")
                return False
            
            # Step 3: Start monitoring with individual listeners
            logger.info("👂 Starting individual listeners...")
            monitoring_started = await self.monitor.start_monitoring()
            if not monitoring_started:
                logger.error("❌ Failed to start monitoring")
                return False
            
            self.is_running = True
            
            logger.info(
                "✅ Telegram Listener Service started successfully (Fast Mode)",
                channels_monitoring=len(channels),
                service_status="active",
                connection_optimized=True,
                individual_listeners=True
            )
            
            # Log service details
            logger.info("📊 Service Configuration:")
            logger.info(f"  • Environment: {settings.environment}")
            logger.info(f"  • User: {self.client.user_info.get('first_name', 'Unknown') if self.client.user_info else 'Unknown'}")
            logger.info(f"  • Channels: {len(channels)}")
            logger.info(f"  • Connection: ConnectionTcpFull (optimized)")
            logger.info(f"  • Updates: sequential_updates=False (concurrent)")
            logger.info(f"  • Listeners: Individual per channel")
            logger.info("  • Status: Fast monitoring active...")
            logger.info("-" * 60)
            
            return True
            
        except Exception as e:
            logger.error("❌ Failed to start listener service", error=str(e))
            return False
    
    async def stop_service(self) -> None:
        """Stop the listener service gracefully"""
        if not self.is_running:
            return
        
        logger.info("🛑 Stopping Telegram Listener Service")
        
        try:
            # Stop monitoring
            await self.monitor.stop_monitoring()
            
            # Disconnect from Telegram
            await self.client.disconnect()
            
            self.is_running = False
            
            # Log final statistics
            monitor_stats = self.monitor.get_monitoring_stats()
            
            logger.info("📊 Final Service Statistics:")
            logger.info(f"  • Total messages captured: {monitor_stats['messages_captured']}")
            logger.info(f"  • Channels monitored: {monitor_stats['total_channels']}")
            logger.info(f"  • Listeners registered: {monitor_stats['listeners_registered']}")
            logger.info("✅ Telegram Listener Service stopped")
            
        except Exception as e:
            logger.error("⚠️ Error during service shutdown", error=str(e))
    
    async def health_check(self) -> dict:
        """
        Get simplified service health status
        
        Returns:
            dict: Service health information
        """
        telegram_health = await self.client.health_check()
        monitor_stats = self.monitor.get_monitoring_stats()
        
        return {
            "service": "telegram-listener-fast",
            "status": "healthy" if self.is_running else "stopped",
            "is_running": self.is_running,
            "mode": "fast_monitoring",
            "telegram": telegram_health,
            "monitoring": monitor_stats,
            "optimizations": {
                "individual_listeners": True,
                "database_overhead": False,
                "connection_type": "ConnectionTcpFull",
                "sequential_updates": False
            }
        }
    
    async def run_forever(self) -> None:
        """Run the service until interrupted with connection monitoring"""
        try:
            # Start the service
            started = await self.start_service()
            if not started:
                logger.error("❌ Failed to start service")
                return
            
            logger.info("🔄 Fast monitoring active - Press Ctrl+C to stop")
            logger.info("⚡ Optimized for maximum speed - no database overhead")
            
            # Enhanced connection monitoring loop
            connection_check_interval = 10  # Check every 10 seconds
            health_log_interval = 60  # Log health every 60 seconds
            last_health_log = 0
            
            try:
                while self.is_running:
                    # Quick connection health check
                    if not self.client.is_connected:
                        logger.warning("📡 Connection lost - attempting reconnect...")
                        reconnected = await self.client.reconnect()
                        if reconnected:
                            logger.info("✅ Reconnected successfully")
                            # Re-register listeners after reconnection
                            if not self.monitor.register_listeners():
                                logger.error("❌ Failed to re-register listeners")
                                break
                        else:
                            logger.error("❌ Failed to reconnect - stopping service")
                            break
                    
                    # Periodic health logging
                    current_time = asyncio.get_event_loop().time()
                    if current_time - last_health_log > health_log_interval:
                        health = await self.health_check()
                        logger.info(
                            "💓 Service Health Check",
                            messages_captured=health['monitoring']['messages_captured'],
                            telegram_status=health['telegram']['status'],
                            listeners_active=health['monitoring']['listeners_registered']
                        )
                        last_health_log = current_time
                    
                    # Short sleep to prevent busy waiting
                    await asyncio.sleep(connection_check_interval)
                    
            except KeyboardInterrupt:
                logger.info("⌨️ Keyboard interrupt received")
            
        except Exception as e:
            logger.error("💥 Unexpected error in service", error=str(e))
        finally:
            await self.stop_service()


@asynccontextmanager
async def lifespan_manager():
    """Simplified lifespan context manager"""
    service = TelegramListenerService()
    
    try:
        # Startup
        started = await service.start_service()
        if started:
            yield service
        else:
            raise RuntimeError("Failed to start Fast Telegram Listener Service")
    finally:
        # Shutdown
        await service.stop_service()


async def main():
    """Main entry point for the fast listener service"""
    logger.info("🎬 Telegram Listener Service (Fast Mode) - Starting...")
    logger.info("⚡ Optimized for maximum speed with individual listeners")
    
    service = TelegramListenerService()
    await service.run_forever()


if __name__ == "__main__":
    # Configure logging for standalone execution
    import logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the fast service
    asyncio.run(main())