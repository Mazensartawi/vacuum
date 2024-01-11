#!/usr/bin/python
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)
GPIO.setup(16, GPIO.OUT)
GPIO.setup(18, GPIO.OUT)
GPIO.setwarnings(False)
GPIO.output(16, True)


def SpinMotor(direction, num_steps):
    p = GPIO.PWM(16, 1000)  # Set the PWM frequency to 1000 Hz
    num_steps = int(num_steps)
    GPIO.output(18, direction)
    p.start(50)  # Start PWM with a duty cycle of 50
    while num_steps > 0:
        time.sleep(0.0005)
        num_steps -= 1
    p.stop()
    GPIO.cleanup()


num_steps = 8
direction_input = input('Direction (L or R):')
degree = input('Degree: ')
num_steps = int(degree) * int(num_steps)

if direction_input == 'L':
    SpinMotor(True, num_steps)
else:
    SpinMotor(False, num_steps)
