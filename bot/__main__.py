"""Bot entry point - minimal version for Railway."""

import asyncio
import logging
import os
import sys

from aiohttp import web

# Setup logging FIRST
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
    force=True,
)
logger = logging.getLogger(__name__)


async def health_check(request):
    """Health check endpoint."""
    logger.info("Health check request received")
    return web.Response(text="OK", status=200)


async def root_handler(request):
    """Root endpoint."""
    return web.Response(text="ALBOT is running", status=200)


async def start_web_server():
    """Start minimal web server."""
    port = int(os.getenv("PORT", 8080))

    logger.info("=" * 60)
    logger.info(f"Starting ALBOT web server on 0.0.0.0:{port}")
    logger.info("=" * 60)

    app = web.Application()
    app.router.add_get("/health", health_check)
    app.router.add_get("/", root_handler)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logger.info(f"✅ Web server started successfully on 0.0.0.0:{port}")
    logger.info(f"✅ Health endpoint: http://0.0.0.0:{port}/health")
    logger.info("=" * 60)

    # Keep running forever
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await runner.cleanup()


async def start_bot():
    """Start bot (disabled for now)."""
    logger.info("Bot polling disabled - web server only mode")
    # Will add bot later after web server works
    await asyncio.sleep(3600 * 24)  # Sleep for 24h


async def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("ALBOT STARTING")
    logger.info("=" * 60)

    # Start only web server for now
    await start_web_server()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"FATAL ERROR: {e}", exc_info=True)
        sys.exit(1)
