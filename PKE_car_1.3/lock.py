import RPi.GPIO as GPIO
from time import sleep

#GPIO pin used
SERVO_PWM_PIN = 18

#init
GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_PWM_PIN, GPIO.OUT)
pwm = GPIO.PWM(SERVO_PWM_PIN, 50)
pwm.start(0)

def lock():
    duty = 2
    rotate_lock(duty)
    print("Locking")
    sleep(0.5)

def unlock():
    duty = 13
    print("Unlocking")
    rotate_lock(duty)
    sleep(0.5)

def rotate_lock(duty):
    #send pwm signal to turn servo
    GPIO.output(SERVO_PWM_PIN, True)
    pwm.ChangeDutyCycle(duty)
    sleep(0.5)
    GPIO.output(SERVO_PWM_PIN, False)
    pwm.ChangeDutyCycle(0) #bit of cleanup to avoid jitter