import cv2
import os

class Capture:
    def __init__(self, source=0):
        try:
            cap = cv2.VideoCapture(0, cv2.CAP_V4L)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 240)
            self.cap = cap
            ret, frame = self.cap.read()
            if not ret:
                raise Exception('Could not get frame of capture', source)
        except Exception as e:
            print("Error in Capture.py: ", str(e))
            return
        print("Sucessfully opened capture with id", source)

    def get_frame(self):
        return self.cap.read()

    def release(self):
        self.cap.release()

    def detect_and_move(self):
        roi_width = 400
        roi_height = 300
        color_lower = np.array([0, 100, 100])  
        color_upper = np.array([10, 255, 255])
        densidad_umbral = 10

        ret, frame = self.get_frame()
        if not ret:
            print("Error: No se pudo capturar la imagen.")
            return None 

        height, width, _ = frame.shape
        roi_width = min(roi_width, width)
        roi_height = min(roi_height, height)

        x_start = (width - roi_width) // 2
        y_start = (height - roi_height) // 2
        x_end = x_start + roi_width
        y_end = y_start + roi_height

        roi_frame = frame[y_start:y_end, x_start:x_end]

        third_width = roi_width // 3
        left_section = roi_frame[:, :third_width]
        middle_section = roi_frame[:, third_width:2 * third_width]
        right_section = roi_frame[:, 2 * third_width:]

        def process_section(section):
            gray = cv2.cvtColor(section, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blurred, 50, 150)

            kernel = np.ones((3, 3), np.uint8)
            dilated = cv2.dilate(edges, kernel, iterations=1)
            eroded = cv2.erode(dilated, kernel, iterations=1)
            closed = cv2.morphologyEx(eroded, cv2.MORPH_CLOSE, kernel)

            contornos, _ = cv2.findContours(closed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            return len(contornos)

        def detectar_color(frame):
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, color_lower, color_upper)
            contornos, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            area_total = sum(cv2.contourArea(cnt) for cnt in contornos)
            return area_total > 3000 

        left_count = process_section(left_section)
        center_count = process_section(middle_section)
        right_count = process_section(right_section)

        if max(left_count, center_count, right_count) > densidad_umbral:
            print("Alta densidad de contornos, deteniendo y buscando área abierta.")
            return "stop"  

        if left_count < center_count and left_count < right_count:
            print("Menos obstáculos a la izquierda, girando a la izquierda.")
            return "left" 
        elif center_count <= left_count and center_count <= right_count:
            print("Camino libre al centro, avanzando.")
            return "forward" 
        elif right_count < left_count and right_count < center_count:
            print("Menos obstáculos a la derecha, girando a la derecha.")
            return "right"  
        else:
            print("Deteniendo para evitar cambios rápidos.")
            return "stop"  

        if detectar_color(frame):
            print("Gran presencia de color rojo detectada, deteniendo.")
            return "stop" 
