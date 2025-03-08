import cv2
import numpy as np
import time
import platform
import os
import requests



import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

MOTOR_IZQUIERDO = 17
MOTOR_DERECHO = 27

GPIO.setup(MOTOR_IZQUIERDO, GPIO.OUT)
GPIO.setup(MOTOR_DERECHO, GPIO.OUT)

def activar_motor_izquierdo():
    GPIO.output(MOTOR_IZQUIERDO, GPIO.HIGH)
    GPIO.output(MOTOR_DERECHO, GPIO.LOW)
    print("[GPIO] Motor izquierdo activado")

def activar_motor_derecho():
    GPIO.output(MOTOR_IZQUIERDO, GPIO.LOW)
    GPIO.output(MOTOR_DERECHO, GPIO.HIGH)
    print("[GPIO] Motor derecho activado")

def activar_ambos_motores():
    GPIO.output(MOTOR_IZQUIERDO, GPIO.HIGH)
    GPIO.output(MOTOR_DERECHO, GPIO.HIGH)
    print("[GPIO] Ambos motores activados")

def detener_motores():
    GPIO.output(MOTOR_IZQUIERDO, GPIO.LOW)
    GPIO.output(MOTOR_DERECHO, GPIO.LOW)
    print("[GPIO] Motores detenidos")

def main():
    roi_width = 400
    roi_height = 300
    color_lower = np.array([0, 100, 100])  # Color rojo en HSV
    color_upper = np.array([10, 255, 255])
    densidad_umbral = 10

    # Reducir resolución de captura para mejorar rendimiento
    if platform.system() == 'Linux':
        cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    else:
        cap = cv2.VideoCapture(0)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

    if not cap.isOpened():
        print("Error: No se pudo abrir la cámara.")
        return

    cv2.namedWindow('Camara en Vivo')
    cv2.namedWindow('Contornos Izquierda')
    cv2.namedWindow('Contornos Centro')
    cv2.namedWindow('Contornos Derecha')

    last_message_time = time.time()
    message_delay = 0.5
    modo_busqueda_color = False

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: No se pudo capturar la imagen.")
                break

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
                cv2.drawContours(section, contornos, -1, (0, 0, 255), 2)
                return len(contornos)

            def detectar_color(frame):
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                mask = cv2.inRange(hsv, color_lower, color_upper)
                contornos, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                area_total = sum(cv2.contourArea(cnt) for cnt in contornos)
                return area_total > 3000  # Reducción del umbral para mejor respuesta

            left_count = process_section(left_section)
            center_count = process_section(middle_section)
            right_count = process_section(right_section)

            current_time = time.time()

            if not modo_busqueda_color:
                if max(left_count, center_count, right_count) > densidad_umbral:
                    print("Alta densidad de contornos, deteniendo y buscando área abierta.")
                    detener_motores()
                    while True:
                        activar_motor_izquierdo()
                        ret, frame = cap.read()
                        if not ret:
                            break
                        left_count = process_section(left_section)
                        center_count = process_section(middle_section)
                        right_count = process_section(right_section)
                        if min(left_count, center_count, right_count) <= densidad_umbral:
                            print("Área abierta detectada, buscando color rojo.")
                            modo_busqueda_color = True
                            break
                    detener_motores()
                else:
                    if left_count < center_count and left_count < right_count:
                        print("Menos obstáculos a la izquierda, girando a la izquierda.")
                        activar_motor_izquierdo()
                    elif center_count <= left_count and center_count <= right_count:
                        print("Camino libre al centro, avanzando.")
                        activar_ambos_motores()
                    elif right_count < left_count and right_count < center_count:
                        print("Menos obstáculos a la derecha, girando a la derecha.")
                        activar_motor_derecho()
                    else:
                        print("Deteniendo para evitar cambios rápidos.")
                        detener_motores()

            else:
                print("Buscando color rojo.")
                activar_motor_izquierdo()
                if detectar_color(frame):
                    print("Gran presencia de color rojo detectada, deteniendo.")
                    detener_motores()
                    modo_busqueda_color = False

            time.sleep(0.01)  # Pausa breve para reducir carga en CPU

            cv2.imshow('Camara en Vivo', roi_frame)
            cv2.imshow('Contornos Izquierda', left_section)
            cv2.imshow('Contornos Centro', middle_section)
            cv2.imshow('Contornos Derecha', right_section)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                detener_motores()
                break

    finally:
        detener_motores()
        cap.release()
        cv2.destroyAllWindows()
        if is_raspberry_pi():
            GPIO.cleanup()

if __name__ == "__main__":
    main()

