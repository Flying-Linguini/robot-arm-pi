from adafruit_servokit import ServoKit		# works with PCA9685 servo controller
import inputs
import math
import time
import threading
from RPi import GPIO
from subprocess import call
import os
import sys
import serial

print("starting")

working = True				# false when program stops

DIR1_PIN = 6				# pins for direction and step in stepper motor
STEP1_PIN = 25

CW = 1 						# constants for clockwise/counterclockwise
CCW = 0

STEPS_PER_REV = 200			# for steppers
STEP_DELAY = 0.0005 / 1		# found experimentally. seems to sork pretty well (divided by resolution)

GPIO.setmode(GPIO.BCM)

GPIO.setup(DIR1_PIN, GPIO.OUT)
GPIO.setup(STEP1_PIN, GPIO.OUT)



class StepperDriver():
	# handles one stepper motor each instance. this must be handled on main thread for GPIO allocation reasons
	def __init__(self, dir_pin, step_pin, enc_idx, precision, delay):
		global CW

		self.dir_pin = dir_pin
		self.step_pin = step_pin
		self.enc_idx = enc_idx
		self.precision = precision 			# motor stops moving when within precision of target

		self.state = 0						# initial state
		self.target = 0

		self.step_state = 0					# 1 or 0 for stepping high or low (< 0 for waiting)
		self.step_delay = delay				# motor skips steps this many times

		GPIO.output(self.dir_pin, CW)		# initial direction

	def get_state(self):
		# get encoder state from serial
		self.state = 0

	def update(self, target):
		# give motor new target
		self.target = target

	def check_step(self):
		# thread running stepper motors
		global CW, CCW

		self.get_state()

		# direction
		if self.target > self.state:
			GPIO.output(self.dir_pin, CW)

		elif self.target < self.state:
			GPIO.output(self.dir_pin, CCW)

		# keep step delays from getting stuck really long
		#if self.step_state < self.step_delay:
		#	self.step_state = -self.step_delay

	def step(self):
		print(self.step_state)

		if abs(self.state - self.target) > self.precision:
			if self.step_state == 0:
				# go high
				GPIO.output(self.step_pin, GPIO.HIGH)
				self.step_state = 1

			elif self.step_state == 1:
				# go low
				GPIO.output(self.step_pin, GPIO.LOW)
				self.step_state = -self.step_delay

			elif self.step_state < 0:
				# wait to limit speed
				self.step_state += 1


"""while True:
	for s in joints.steppers:
		#s.check_step()
		s.step()

	time.sleep(STEP_DELAY)"""


s = StepperDriver(DIR1_PIN, STEP1_PIN, 0, 5, 0)
s.target = 6		# CW rotation for test
s.check_step()


time.sleep(1)		# give encoders time to average out true

now = time.time()

try:
	while working:
		then = now
		now = time.time()

		# ensure proper timing for steppers
		while now - then < STEP_DELAY:
			time.sleep(0.00001)
			now = time.time()

		print((now - then))

		# step stepper
		s.step()


except KeyboardInterrupt:
	print("stopping")

GPIO.cleanup()
