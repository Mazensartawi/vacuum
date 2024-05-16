import time
import RPi.GPIO as GPIO

# Constants for motor pins
MOTOR_1_PIN_1 = 11
MOTOR_1_PIN_2 = 13
MOTOR_2_PIN_1 = 16
MOTOR_2_PIN_2 = 18

# Ultrasonic sensor pins
ULTRASONIC_LEFT_TRIGGER = 38
ULTRASONIC_LEFT_ECHO = 40
ULTRASONIC_FRONT_TRIGGER = 5
ULTRASONIC_FRONT_ECHO = 3
ULTRASONIC_RIGHT_TRIGGER = 23
ULTRASONIC_RIGHT_ECHO = 21

# Threshold distances in centimeters
TOO_CLOSE_WALL = 18.0
TOO_FAR_WALL = 25.0
TOO_CLOSE_FRONT = 10.0

# Time to turn 90 degrees (in seconds)
TURNING_TIME = 2.24

# Threshold distances in centimeters
TOO_CLOSE_WALL = 18.0
TOO_FAR_WALL = 25.0
TOO_CLOSE_FRONT = 10.0

# Time to turn 90 degrees (in seconds)
TURNING_TIME = 2.24

def setup_gpio():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup([MOTOR_1_PIN_1, MOTOR_1_PIN_2, MOTOR_2_PIN_1, MOTOR_2_PIN_2], GPIO.OUT)
    GPIO.setup(ULTRASONIC_FRONT_TRIGGER, GPIO.OUT)
    GPIO.setup(ULTRASONIC_FRONT_ECHO, GPIO.IN)
    GPIO.setup(ULTRASONIC_LEFT_TRIGGER, GPIO.OUT)
    GPIO.setup(ULTRASONIC_LEFT_ECHO, GPIO.IN)
    GPIO.setup(ULTRASONIC_RIGHT_TRIGGER, GPIO.OUT)
    GPIO.setup(ULTRASONIC_RIGHT_ECHO, GPIO.IN)
    print("GPIO setup complete")

def cleanup_gpio():
    GPIO.cleanup()
    print("GPIO cleaned up")

def move_forward():
    GPIO.output(MOTOR_1_PIN_1, True)
    GPIO.output(MOTOR_1_PIN_2, False)
    GPIO.output(MOTOR_2_PIN_1, True)
    GPIO.output(MOTOR_2_PIN_2, False)
    print("Moving forward")

def move_backward():
    GPIO.output(MOTOR_1_PIN_1, False)
    GPIO.output(MOTOR_1_PIN_2, True)
    GPIO.output(MOTOR_2_PIN_1, False)
    GPIO.output(MOTOR_2_PIN_2, True)
    print("Moving backward")

def turn_left():
    GPIO.output(MOTOR_1_PIN_1, False)
    GPIO.output(MOTOR_1_PIN_2, True)
    GPIO.output(MOTOR_2_PIN_1, True)
    GPIO.output(MOTOR_2_PIN_2, False)
    print("Turning left")

def turn_right():
    GPIO.output(MOTOR_1_PIN_1, True)
    GPIO.output(MOTOR_1_PIN_2, False)
    GPIO.output(MOTOR_2_PIN_1, False)
    GPIO.output(MOTOR_2_PIN_2, True)
    print("Turning right")

def stop_motors():
    GPIO.output(MOTOR_1_PIN_1, False)
    GPIO.output(MOTOR_1_PIN_2, False)
    GPIO.output(MOTOR_2_PIN_1, False)
    GPIO.output(MOTOR_2_PIN_2, False)
    print("Motors stopped")

def get_distance(trigger_pin, echo_pin):
    GPIO.output(trigger_pin, True)
    time.sleep(0.00001)
    GPIO.output(trigger_pin, False)

    pulse_start = time.time()
    pulse_end = time.time()

    print(f"Measuring distance on trigger pin {trigger_pin} and echo pin {echo_pin}")

    while GPIO.input(echo_pin) == 0:
        pulse_start = time.time()
        if time.time() - pulse_start > 0.04:  # Timeout after 40 ms
            print(f"Timeout waiting for echo signal to start (pin {trigger_pin})")
            return -1

    while GPIO.input(echo_pin) == 1:
        pulse_end = time.time()
        if time.time() - pulse_end > 0.04:  # Timeout after 40 ms
            print(f"Timeout waiting for echo signal to end (pin {trigger_pin})")
            return -1

    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150  # Speed of sound in cm/s
    distance = round(distance, 2)
    print(f"Distance measured: {distance} cm on trigger pin {trigger_pin}")
    return distance

def main():
    try:
        setup_gpio()

        while True:
            print("Starting distance measurement")
            front_distance = get_distance(ULTRASONIC_FRONT_TRIGGER, ULTRASONIC_FRONT_ECHO)
            left_distance = get_distance(ULTRASONIC_LEFT_TRIGGER, ULTRASONIC_LEFT_ECHO)
            right_distance = get_distance(ULTRASONIC_RIGHT_TRIGGER, ULTRASONIC_RIGHT_ECHO)

            print(f"Front distance: {front_distance} cm, Left distance: {left_distance} cm, Right distance: {right_distance} cm")

            if front_distance == -1 or left_distance == -1 or right_distance == -1:
                print("Error reading distance, skipping this cycle")
                continue

            if front_distance < TOO_CLOSE_FRONT:
                stop_motors()
                move_backward()
                time.sleep(0.5)
                stop_motors()
                turn_right()
                time.sleep(0.8)
                stop_motors()
                move_forward()
                time.sleep(1.7)
                continue

            if TOO_CLOSE_WALL < left_distance < TOO_FAR_WALL:
                move_forward()
                print("Drive forward")
                time.sleep(0.1)
                continue

            if left_distance <= TOO_CLOSE_WALL:
                stop_motors()
                turn_right()
                time.sleep(0.5)
                stop_motors()
                move_forward()
                time.sleep(1)
                continue

            if left_distance >= TOO_FAR_WALL:
                stop_motors()
                turn_left()
                time.sleep(0.5)
                stop_motors()
                move_forward()
                time.sleep(1)
                continue

    except KeyboardInterrupt:
        pass
    finally:
        cleanup_gpio()

if __name__ == "__main__":
    main()
