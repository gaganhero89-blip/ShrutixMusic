import asyncio
import importlib
import os
import sys
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from pyrogram import idle
from pytgcalls.exceptions import NoActiveGroupCall

# Raise the file descriptor limit on Linux to avoid "[Errno 24] Too many open files"
if sys.platform != "win32":
    try:
        import resource
        _soft, _hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        _target = min(65536, _hard)
        if _soft < _target:
            resource.setrlimit(resource.RLIMIT_NOFILE, (_target, _hard))
    except Exception:
        pass

import config
from ShrutixMusic import LOGGER, nand, userbot
from ShrutixMusic.core.call import Shruti
from ShrutixMusic.misc import sudo
from ShrutixMusic.plugins import ALL_MODULES
from ShrutixMusic.utils.database import get_banned_users, get_gbanned
from config import BANNED_USERS


# HTTP Server for Render health checks - PERFECTLY DETECTABLE
class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for Render health checks"""
    
    def do_GET(self):
        """Handle GET requests"""
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.send_header('Content-Length', '22')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(b'ShrutixMusic Bot OK!')
    
    def log_message(self, format, *args):
        """Suppress log messages to keep console clean"""
        pass


def run_http_server():
    """Run HTTP server that Render WILL detect"""
    port = int(os.environ.get("PORT", 10000))
    server_address = ('0.0.0.0', port)
    
    # Create socket first to ensure proper binding
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(server_address)
    sock.listen(128)
    
    httpd = HTTPServer(server_address, HealthCheckHandler)
    httpd.socket = sock
    httpd.timeout = 0.5  # Non-blocking
    
    LOGGER(__name__).info(f"🌐 HTTP server listening on 0.0.0.0:{port}")
    LOGGER(__name__).info(f"🌐 Health check: http://localhost:{port}/")
    LOGGER(__name__).info("✅ Render port detection ready!")
    
    try:
        while True:
            httpd.handle_request()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        LOGGER(__name__).error(f"HTTP server error: {e}")
    finally:
        httpd.server_close()
        sock.close()


async def main():
    try:
        # Step 1: Validate required environment variables
        if (
            not config.STRING1
            and not config.STRING2
            and not config.STRING3
            and not config.STRING4
            and not config.STRING5
        ):
            LOGGER(__name__).error("❌ Assistant client variables not defined, exiting...")
            return

        LOGGER(__name__).info("🚀 Starting ShrutixMusic Bot...")

        # Step 2: Start HTTP server FIRST (for Render port detection)
        http_thread = threading.Thread(target=run_http_server, daemon=True)
        http_thread.start()
        LOGGER(__name__).info("🌐 HTTP server thread started for Render health checks")

        # Step 3: Load banned users from database
        try:
            users = await get_gbanned()
            for user_id in users:
                BANNED_USERS.add(user_id)
            users = await get_banned_users()
            for user_id in users:
                BANNED_USERS.add(user_id)
            LOGGER(__name__).info("✅ Banned users loaded from database")
        except Exception as e:
            LOGGER(__name__).warning(f"⚠️ Could not load banned users: {e}")

        # Step 4: Load sudo users
        await sudo()
        LOGGER(__name__).info("✅ Sudo users loaded")

        # Step 5: Start assistant clients
        await nand.start()
        LOGGER(__name__).info("✅ Assistant clients started")

        # Step 6: Load all plugin modules
        loaded_modules = 0
        for all_module in ALL_MODULES:
            try:
                importlib.import_module("ShrutixMusic.plugins" + all_module)
                loaded_modules += 1
            except Exception as e:
                LOGGER("ShrutixMusic.plugins").error(f"Failed to load module {all_module}: {e}")
        LOGGER("ShrutixMusic.plugins").info(f"✅ Loaded {loaded_modules}/{len(ALL_MODULES)} modules")

        # Step 7: Start main userbot
        await userbot.start()
        LOGGER(__name__).info("✅ Main userbot started")

        # Step 8: Initialize voice call handler
        await Shruti.start()
        LOGGER(__name__).info("✅ PyTgCalls client started")

        # Step 9: Test voice call setup
        try:
            await Shruti.stream_call("https://te.legra.ph/file/29f784eb49d230ab62e9e.mp4")
            LOGGER(__name__).info("✅ Voice call test passed")
        except NoActiveGroupCall:
            LOGGER("ShrutixMusic").error(
                "❌ Please turn on videochat in your log group/channel. Stopping..."
            )
            return
        except Exception as e:
            LOGGER(__name__).warning(f"⚠️ Voice call test failed (non-critical): {e}")

        # Step 10: Setup decorators
        await Shruti.decorators()
        LOGGER(__name__).info("✅ Decorators setup complete")

        # Step 11: Success message
        LOGGER("ShrutixMusic").info(
            "\x53\x68\x72\x75\x74\x69\x78\x20\x4d\x75\x73\x69\x63\x20\x42\x6f\x74\x20\x53\x74\x61\x72\x74\x65\x64\x20\x53\x75\x63\x63\x65\x73\x73\x66\x75\x6c\x6c\x79\x2e\n\n"
            "\x44\x6f\x6e'\x74\x20\x66\x6f\x72\x67\x65\x74\x20\x74\x6f\x20\x76\x69\x73\x69\x74\x20\x40\x53\x68\x72\x75\x74\x69\x42\x6f\x74\x73\n"
            "✅ Bot fully operational! 🎵"
        )

        # Step 12: Keep bot running
        try:
            await idle()
        except KeyboardInterrupt:
            LOGGER("ShrutixMusic").info("👋 Received stop signal...")
        except Exception as e:
            LOGGER("ShrutixMusic").error(f"❌ Error during idle: {e}")

        # Step 13: Cleanup
        await nand.stop()
        await userbot.stop()
        LOGGER("ShrutixMusic").info("🛑 ShrutixMusic Music Bot stopped gracefully")
        
    except Exception as e:
        LOGGER("ShrutixMusic").critical(f"💥 Critical error in main: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    loop = None
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        LOGGER("ShrutixMusic").info("👋 Bot stopped by user (Ctrl+C)")
    except SystemExit as e:
        LOGGER("ShrutixMusic").error(f"💥 Bot exited with system error: {e}")
        raise
    except Exception as e:
        LOGGER("ShrutixMusic").critical(f"💥 Unexpected error: {e}", exc_info=True)
    finally:
        # Clean shutdown
        if loop and loop.is_running():
            loop.stop()
            loop.close()
        LOGGER("ShrutixMusic").info("🏁 Bot process ended")
