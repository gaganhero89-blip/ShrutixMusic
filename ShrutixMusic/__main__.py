import asyncio
import importlib
import os
import sys
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


# HTTP Server for Render health checks
class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for Render health checks"""
    
    def do_GET(self):
        """Handle GET requests"""
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'ShrutixMusic Bot is running')
    
    def log_message(self, format, *args):
        """Suppress log messages to keep console clean"""
        pass


def run_http_server():
    """Run a simple HTTP server for Render health checks"""
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    LOGGER(__name__).info(f"🌐 HTTP health check server started on port {port}")
    server.serve_forever()


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
            LOGGER(__name__).error("Assistant client variables not defined, exiting...")
            return

        # Step 2: Start HTTP server in a separate thread (for Render)
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
        except:
            pass

        # Step 4: Load sudo users
        await sudo()

        # Step 5: Start assistant/userbot clients
        await nand.start()
        
        # Step 6: Load all plugin modules
        for all_module in ALL_MODULES:
            try:
                importlib.import_module("ShrutixMusic.plugins" + all_module)
            except Exception as e:
                LOGGER("ShrutixMusic.plugins").error(f"Failed to load module {all_module}: {e}")
        LOGGER("ShrutixMusic.plugins").info("Successfully Imported Modules...")

        # Step 7: Start main userbot
        await userbot.start()
        
        # Step 8: Initialize voice call handler
        await Shruti.start()
        
        # Step 9: Test voice call setup
        try:
            await Shruti.stream_call("https://te.legra.ph/file/29f784eb49d230ab62e9e.mp4")
        except NoActiveGroupCall:
            LOGGER("ShrutixMusic").error(
                "Please turn on the videochat of your log group\channel.\n\nStopping Bot..."
            )
            return
        except:
            pass
        
        # Step 10: Setup decorators
        await Shruti.decorators()
        
        LOGGER("ShrutixMusic").info(
            "\x53\x68\x72\x75\x74\x69\x78\x20\x4d\x75\x73\x69\x63\x20\x42\x6f\x74\x20\x53\x74\x61\x72\x74\x65\x64\x20\x53\x75\x63\x63\x65\x73\x73\x66\x75\x6c\x6c\x79\x2e\n\n\x44\x6f\x6e'\x74\x20\x66\x6f\x72\x67\x65\x74\x20\x74\x6f\x20\x76\x69\x73\x69\x74\x20\x40\x53\x68\x72\x75\x74\x69\x42\x6f\x74\x73"
        )

        # Step 11: Keep the bot running
        try:
            await idle()
        except KeyboardInterrupt:
            LOGGER("ShrutixMusic").info("Received stop signal...")
        except Exception as e:
            LOGGER("ShrutixMusic").error(f"Error during idle: {e}")
        
        # Step 12: Cleanup
        await nand.stop()
        await userbot.stop()
        LOGGER("ShrutixMusic").info("Stopping ShrutixMusic Music Bot...")
        
    except Exception as e:
        LOGGER("ShrutixMusic").error(f"Critical error in main: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        LOGGER("ShrutixMusic").info("Bot stopped by user (Ctrl+C)")
    except SystemExit as e:
        LOGGER("ShrutixMusic").error(f"Bot exited with system error: {e}")
        raise
    except Exception as e:
        LOGGER("ShrutixMusic").error(f"Unexpected error caused bot to stop: {e}", exc_info=True)
    finally:
        # Ensure cleanup happens
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.stop()
        except:
            pass
