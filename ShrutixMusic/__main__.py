import asyncio
import os
import sys
import socket
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

# IMPORTS AFTER HTTP SERVER
from pyrogram import idle
from pytgcalls.exceptions import NoActiveGroupCall

import config
from ShrutixMusic import LOGGER, nand, userbot
from ShrutixMusic.core.call import Shruti
from ShrutixMusic.misc import sudo
from ShrutixMusic.plugins import ALL_MODULES
from ShrutixMusic.utils.database import get_banned_users, get_gbanned
from config import BANNED_USERS

# PORT 8000 HTTP SERVER - STARTS IMMEDIATELY
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Content-Length', '19')
        self.end_headers()
        self.wfile.write(b'ShrutixMusic OK!')
        print(f"🌐 [Port 8000] Health check OK!")
    
    def log_message(self, *args): pass

def http_server_forever():
    """BLOCKING HTTP Server - Render detects immediately"""
    port = int(os.environ.get('PORT', 8000))
    httpd = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"🚀 Port 8000 LIVE: http://0.0.0.0:{port}")
    print("✅ Render will detect port NOW!")
    httpd.serve_forever()

# START HTTP SERVER IN MAIN THREAD FIRST
if __name__ == "__main__":
    print("🎵 Starting ShrutixMusic with Port 8000...")
    
    # START HTTP SERVER IMMEDIATELY (Main thread)
    server_thread = threading.Thread(target=http_server_forever, daemon=False)
    server_thread.start()
    
    # Wait 2 seconds for port binding
    time.sleep(2)
    
    # NOW start bot in event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("👋 Bot stopped")
    finally:
        loop.close()

async def main():
    try:
        print("🤖 Starting bot services...")
        
        # Your existing bot code here...
        if not config.STRING1 or not config.STRING2:
            print("❌ Missing API credentials")
            return
            
        await sudo()
        
        # Load banned users
        try:
            users = await get_banned_users()
            for user_id in users:
                BANNED_USERS.add(user_id)
        except:
            pass
            
        await nand.start()
        
        # Load plugins
        for module in ALL_MODULES:
            importlib.import_module("ShrutixMusic.plugins" + module)
        print("✅ All modules loaded")
        
        await userbot.start()
        await Shruti.start()
        
        try:
            await Shruti.stream_call("https://te.legra.ph/file/29f784eb49d230ab62e9e.mp4")
        except:
            pass
            
        await Shruti.decorators()
        print("🎉 ShrutixMusic Bot Started Successfully!")
        print("🌐 Port 8000: https://your-app.onrender.com/")
        
        await idle()
        
    except Exception as e:
        print(f"❌ Error: {e}")
