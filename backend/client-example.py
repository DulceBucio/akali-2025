#!/usr/bin/env python3
'''Minimal WebSocket client for RPLidar data - prints received information only'''
import asyncio
import json
import websockets
import time

async def run_client(uri="ws://localhost:8801", duration=60):
    """
    Connect to the LiDAR WebSocket server and print received data.
    
    Args:
        uri: WebSocket server URI
        duration: How long to run in seconds
    """
    try:
        print(f"Connecting to {uri}...")
        
        # Connect to the WebSocket server
        async with websockets.connect(
            uri,
            ping_interval=20,
            ping_timeout=60
        ) as websocket:
            print(f"Connected to {uri}")
            
            # Send initial message to start data streaming
            await websocket.send("start")
            print("Sent start message")
            
            # Set end time
            end_time = time.time() + duration
            
            # Receive and print data until duration expires
            while time.time() < end_time:
                try:
                    # Receive message with timeout
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    
                    # Parse JSON data
                    data = json.loads(message)
                    
                    # Print summary of received data
                    print(f"Received data: {len(data['angle'])} points")
                    print(f"  Angle range: {min(data['angle']):.1f}° to {max(data['angle']):.1f}°")
                    print(f"  Distance range: {min(data['distance']):.1f} to {max(data['distance']):.1f}")
                    print(f"  Quality range: {min(data['quality'])} to {max(data['quality'])}")
                    print("-" * 40)
                    
                    # Optional: brief pause to make output readable
                    await asyncio.sleep(0.5)
                    
                except asyncio.TimeoutError:
                    print("Timeout waiting for data")
                
    except websockets.exceptions.ConnectionClosed as e:
        print(f"Connection closed: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Minimal LiDAR Client")
    print("Press Ctrl+C to stop")
    
    try:
        # Run for 60 seconds by default
        asyncio.run(run_client(duration=60))
    except KeyboardInterrupt:
        print("\nClient stopped by user")
