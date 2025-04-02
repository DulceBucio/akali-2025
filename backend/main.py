#!/usr/bin/env python3
'''WebSocket server for RPLidar data transmission'''
import asyncio
import json
import time
import threading
from websockets.server import serve
from rplidar import RPLidar

class LidarHandler:
    def __init__(self, port='/dev/ttyUSB0'):
        self.port = port
        self.lidar = None
        self.iterator = None
        self.running = False
        self.latest_scan = None
        self.scan_lock = threading.Lock()
        
    def connect(self):
        try:
            self.lidar = RPLidar(self.port)
            return True
        except Exception as e:
            print(f"Failed to connect to LiDAR: {e}")
            return False
    
    def start_scanning(self):
        """Start scanning in a separate thread to avoid blocking"""
        if not self.lidar:
            if not self.connect():
                return False
        
        self.running = True
        self.scan_thread = threading.Thread(target=self._scan_worker)
        self.scan_thread.daemon = True
        self.scan_thread.start()
        return True
    
    def _scan_worker(self):
        """Worker thread that continuously updates the latest scan data"""
        try:
            self.iterator = self.lidar.iter_scans()
            while self.running:
                try:
                    scan = next(self.iterator)
                    with self.scan_lock:
                        self.latest_scan = scan
                except StopIteration:
                    print("LiDAR scan iteration ended")
                    break
                except Exception as e:
                    print(f"Error in scan iteration: {e}")
                    time.sleep(0.1)  # Prevent tight loop in case of errors
        except Exception as e:
            print(f"Error in scan worker: {e}")
        finally:
            print("Scan worker thread ending")
    
    def get_latest_data(self):
        """Get the most recent scan data in processed format"""
        with self.scan_lock:
            scan = self.latest_scan
            
        if not scan:
            return None
            
        data = {
            'quality': [point[0] for point in scan], 
            'angle': [point[1] for point in scan], 
            'distance': [point[2] for point in scan]
        }
        return data
    
    def disconnect(self):
        """Stop scanning and disconnect from the LiDAR"""
        self.running = False
        if self.scan_thread and self.scan_thread.is_alive():
            self.scan_thread.join(timeout=1.0)
            
        if self.lidar:
            try:
                self.lidar.stop()
                self.lidar.disconnect()
            except Exception as e:
                print(f"Error during disconnect: {e}")
            self.lidar = None


async def websocket_handler(websocket):
    """Handle WebSocket connections"""
    # Create and start the LiDAR handler
    lidar = LidarHandler()
    if not lidar.start_scanning():
        await websocket.close(1011, "Failed to start LiDAR")
        return
    
    print("LiDAR started, waiting for client messages")
    
    try:
        # Wait for first message (can be used for configuration in the future)
        await websocket.recv()
        print("Client connected, sending data")
        
        while True:
            # Get the latest data (non-blocking)
            data = lidar.get_latest_data()
            
            if data:
                # Send data to client
                await websocket.send(json.dumps(data))
                print(f"Sent {len(data['angle'])} data points")
            else:
                print("No data available")
            
            # Brief pause to prevent overwhelming the connection
            await asyncio.sleep(0.1)
            
            # Optional: wait for a ping from client to continue
            # This can help with flow control
            # await websocket.ping()
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # Clean up
        print("Client disconnected, stopping LiDAR")
        lidar.disconnect()


async def main():
    """Start the WebSocket server"""
    async with serve(
        websocket_handler, 
        "", 
        8801,
        ping_interval=20,
        ping_timeout=60
    ) as server:
        print(f"WebSocket server started on port 8801")
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
