import os
import stat
import subprocess
import socket
import time
import asyncio
import websockets
from threading import Thread


class MitmproxyManager:
    WEBSOCKET_PORT = 8765

    def __init__(self, mitmproxy_path, proxy_port, cache_path):
        self.mitmproxy_path = mitmproxy_path
        self.proxy_port = proxy_port
        self.cache_path = cache_path
        self.mitmproxy_process = None
        self.websocket_server = None

    def start_mitmproxy(self):
        """Starts the mitmproxy process with specified configurations, ensuring executable permissions."""
        print("MitmproxyManager: Starting mitmproxy")

        # Ensure mitmproxy_path is executable
        if not os.access(self.mitmproxy_path, os.X_OK):
            os.chmod(self.mitmproxy_path, stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        cmd = [
            self.mitmproxy_path,
            "--set", "upstream_cert=false",
            "--set", "server_replay_kill_extra=true",
            "--set", "server_replay_nopop=true",
            "-S", self.cache_path,
            "-p", str(self.proxy_port),
            "--ssl-insecure"  # Allow insecure SSL connections
        ]

        self.mitmproxy_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL)
        self.wait_for_port_in_use(self.proxy_port)
        print(f"MitmproxyManager: mitmproxy started on port {self.proxy_port}")

    def stop_mitmproxy(self):
        """Stops the mitmproxy process."""
        if self.mitmproxy_process:
            self.mitmproxy_process.terminate()
        print("MitmproxyManager: mitmproxy stopped")
        os._exit(0)

    @staticmethod
    def wait_for_port_in_use(port, timeout=60):
        """Waits for the specified port to be available within a timeout period."""
        for _ in range(int(timeout * 10)):  # checks every 0.1 seconds
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                if sock.connect_ex(('localhost', int(port))) == 0:
                    return
            time.sleep(0.1)
        raise TimeoutError(f"Timed out waiting for mitmproxy to start on port {port}")

    async def websocket_handler(self, websocket, path):
        """Handles incoming WebSocket connections and messages."""
        print(f"New connection from {websocket.remote_address}")
        try:
            async for message in websocket:
                print(f"Received message from {websocket.remote_address}: {message}")
        except websockets.ConnectionClosed as e:
            print(f"Connection closed from {websocket.remote_address} with reason: {e.reason}")
        finally:
            print(f"Connection to {websocket.remote_address} closed")

    async def start_websocket_server(self):
        """Starts the WebSocket server."""
        self.websocket_server = await websockets.serve(self.websocket_handler, "localhost", self.WEBSOCKET_PORT)
        print(f"WebSocket server started on ws://localhost:{self.WEBSOCKET_PORT}")
        await self.websocket_server.wait_closed()

    def start(self):
        """Starts both mitmproxy and the WebSocket server."""
        self.start_mitmproxy()

        # Start the WebSocket server in a separate thread
        websocket_thread = Thread(target=lambda: asyncio.run(self.start_websocket_server()))
        websocket_thread.start()

        # Allow some time for the WebSocket server to be ready
        time.sleep(1)

        # Place any additional code you want to run here
        print("Mitmproxy is running and WebSocket server is ready.")


    def stop(self):
        """Stops mitmproxy and the WebSocket server, then exits the script."""
        # Stop the mitmproxy process
        self.stop_mitmproxy()

        # Close the WebSocket server if it is running
        if self.websocket_server:
            self.websocket_server.close()
            print("WebSocket server closed")

        # Allow some time for everything to close gracefully
        time.sleep(1)

        # Forcefully exit the script
        print("MitmproxyManager: Script is now terminating.")
        os._exit(0)
