from rplidar import RPLidar as OriginalRPLidar, RPLidarException

class LidarHandler:
    def __init__(self, port='/dev/ttyUSB0'):
        self.port = port
        self.lidar = None
        self.connect()
        
    def connect(self):
        try:
            self.lidar = OriginalRPLidar(self.port)
            return True
        except RPLidarException as e:
            print(f"Failed to connect to LiDAR: {e}")
            return False
            
    def scan_data(self):
        try: 
            iterator = self.lidar.iter_scans()
            scan = next(iterator)

            if not scan or len(scan) == 0:
                print("No data received")
                return None
                
            data = {
                'quality': [point[0] for point in scan], 
                'angle': [point[1] for point in scan], 
                'distance': [point[2] for point in scan]
            }
            print(f"Lidar SCAN: {len(scan)} points") 
            return data
        except RPLidarException as e:
            print(f"Error getting scan data: {e}")
            return None
            
    def disconnect(self):
        if self.lidar:
            try:
                self.lidar.stop()
                self.lidar.disconnect()
            except RPLidarException as e:
                print(f"Error during disconnect: {e}")
    
    def handle_exception(self):
        if self.lidar:
            try:
                self.lidar.stop()
                self.lidar.stop_motor()
                self.lidar.disconnect()
                return self.connect()
            except RPLidarException as e:
                print(f"Error during exception handling: {e}")
                return False
