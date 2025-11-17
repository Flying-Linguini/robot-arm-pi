from adafruit_servokit import ServoKit		# works with PCA9685 servo controller
from inputs import get_gamepad
import math
import time
import threading
from RPi import GPIO

print("starting")

ENC1_PIN = 15				# encoder pin for joint 1
ENC2_PIN = 16
ENC3_PIN = 17
ENC5_PIN = 18				# skips joint 4 (just for steppers)

DIR1_PIN = 20
DIR2_PIN = 21
DIR3_PIN = 22
DIR5_PIN = 23

STEP1_PIN = 24
STEP2_PIN = 25
STEP3_PIN = 26
STEP5_PIN = 27

CW = 1
CCW = 0
STEPS_PER_REV = 200			# for steppers
STEP_DELAY = 0.0005 / 1		# found experimentally. seems to sork pretty well (divided by resolution)

STEP_MODE = (14, 15, 16)	# same for all steppers for now
RESOLUTION = {'full': (0, 0, 0),
			'half': (1, 0, 0),
			'1/4': (0, 1, 0),
			'1/8': (1, 1, 0),
			'1/16': (0, 0, 1),
			'1/32': (1, 0, 1)}

GPIO.setmode(GPIO.BCM)
GPIO.setup(STEP_MODE, GPIO.OUT)
GPIO.output(STEP_MODE, RESOLUTION['full'])


class Controller():
	# handles everything itself for now. just make an instance and reference variables where needed

	def __init__(self):
		# input values. reference these for now for controller input
		# joysticks
		self.left_joy_x = 0
		self.left_joy_y = 0
		self.left_thumb = 0
		self.right_joy_x = 0
		self.right_joy_y = 0
		self.right_thumb = 0
		# d-pad
		self.left_dpad = 0
		self.right_dpad = 0
		self.up_dpad = 0
		self.down_dpad = 0
		# triggers
		self.left_trig = 0
		self.right_trig = 0
		# bumpers
		self.left_bump = 0
		self.right_bump = 0
		# buttons
		self.a = 0
		self.b = 0
		self.x = 0
		self.y = 0
		self.select = 0
		self.start = 0

		# wrist tracking
		self.wrist_pitch = 0
		self.wrist_roll = 0

		# start monitor thread
		self._monitor_thread = threading.Thread(target = self._monitor_controller, args = ())
		self._monitor_thread.daemon = True
		self._monitor_thread.start()

	def _monitor_controller(self):
		# thread for monitoring inputs

		# max trigger and joystick values
		MAX_TRIG_VAL = math.pow(2, 8)
		MAX_JOY_VAL = math.pow(2,15)

		while True:
			try:
				events = get_gamepad()
			except:
				# probably no controller connected
				print("no controller connected...")

				time.sleep(1)
				continue

			for event in events:
				# match might not work
				match event.code:
					# joysticks
					case "ABS_X":
						self.left_joy_x = event.state / MAX_JOY_VAL
					case "ABS_Y":
						self.left_joy_y = event.state / MAX_JOY_VAL
					case "BTN_THUMBL":
						self.left_thumb = event.state

					case "ABS_RX":
						self.right_joy_x = event.state / MAX_JOY_VAL
					case "ABS_RY":
						self.right_joy_y = event.state / MAX_JOY_VAL
					case "BTN_THUMBR":
						self.right_thumb = event.state

					# dpad
					case "BTN_TRIGGER_HAPPY1":
						self.left_dpad = event.state
					case "BTN_TRIGGER_HAPPY2":
						self.right_dpad = event.state
					case "BTN_TRIGGER_HAPPY3":
						self.up_dpad = event.state
					case "BTN_TRIGGER_HAPPY4":
						self.down_dpad = event.state

					# triggers
					case "ABS_Z":
						self.left_trig = event.state / MAX_TRIG_VAL
					case "ABS_RZ":
						self.right_trig = event.state / MAX_TRIG_VAL

					# bumpers
					case "BTN_TL":
						self.left_bump = event.state
					case "BTN_TR":
						self.right_bump = event.state

					# buttons
					case "BTN_SOUTH":
						self.a = event.state
					case "BTN_NORTH":
						self.y = event.state
					case "BTN_EAST":
						self.b = event.state
					case "BTN_WEST":
						self.x = event.state
					case "BTN_SELECT":
						self.select = event.state
					case "BTN_START":
						self.start = event.state

					# what else could be inputted? beats me, but things always happen
					case _:
						print("unknown controller input")


class StepperDriver():
	# handles one stepper motor each instance
	def __init__(self, dir_pin, step_pin, enc_pin, precision):
		global CW

		self.dir_pin = dir_pin
		self.step_pin = step_pin
		self.enc_pin = enc_pin
		self.precision = precision 			# motor stops moving when within precision of target

		self.state = 0						# initial state
		self.target = 0

		GPIO.setup(self.dir_pin, GPIO.OUT)
		GPIO.setup(self.step_pin, GPIO.OUT)
		GPIO.setup(self.enc_pin, GPIO.IN)

		GPIO.output(self.dir_pin, CW)		# initial direction

		# start motor running thread
		self._monitor_thread = threading.Thread(target = self._run_steppers, args = ())
		self._monitor_thread.daemon = True
		self._monitor_thread.start()

	def get_state(self):
		self.state = GPIO.input(self.enc_pin)			# !! might have to do more to get encoder state !!

	def update(self, target):
		# give motor new target
		self.target = target

	def _run_steppers(self):
		# thread running stepper motors
		global CW, CCW, STEP_DELAY

		while True:
			self.get_state()

			# direction
			if self.target > self.state:
				GPIO.output(self.dir_pin, CW)

			elif self.target < self.state:
				GPIO.output(self.dir_pin, CCW)

			# move in direction
			if math.abs(self.state - self.target) > self.precision:
				GPIO.output(self.step_pin, GPIO.HIGH)
				time.sleep(STEP_DELAY)
				GPIO.output(self.step_pin, GPIO.LOW)
				time.sleep(STEP_DELAY)

			else:
				time.sleep(0.01)



class Joints():
	def __init__(self, pin1, pin2, pin3, pin4, pin5, pin6):
		self.state = [0, 0, 0, 0, 0, 0, 0]			# current state of all joints
		self.cont_state = [0, 0, 0, 0, 0, 0, 0]		# state controller for each joint
		self.target = [0, 0, 0, 0, 0, 0, 0]			# target angles of all joints

		# servo stuff
		self.servos = ServoKit(channels=16)			# for joints 4, 5, and 6

		self.servos.frequency = 60

		self.servos.servo[0].set_pulse_width_range(1000, 2000)
		self.servos.servo[1].set_pulse_width_range(1000, 2000)
		self.servos.servo[2].set_pulse_width_range(1000, 2000)

		# stepper stuff
		self.steppers = []
		self.steppers.append(StepperDriver(DIR1_PIN, STEP1_PIN, ENC1_PIN, 5))
		self.steppers.append(StepperDriver(DIR2_PIN, STEP2_PIN, ENC2_PIN, 5))
		self.steppers.append(StepperDriver(DIR3_PIN, STEP3_PIN, ENC3_PIN, 5))
		self.steppers.append(StepperDriver(DIR5_PIN, STEP5_PIN, ENC5_PIN, 5))

	def get_controller_state(self, joy):
		# base
		self.cont_state[0] = joy.left_joy_x
		self.cont_state[1] = joy.left_joy_y

		# mid-arm
		self.cont_state[2] = joy.right_joy_y
		self.cont_state[3] = joy.right_joy_x

		# wrist
		if joy.right_trig > 0:
			self.cont_state[4] = joy.right_trig
		else:
			self.cont_state[4] = -joy.left_trig

		if joy.right_bump > 0:
			self.cont_state[5] = joy.right_bump
		else:
			self.cont_state[5] = joy.left_bump

		# tooling
		if joy.a > 0:
			self.cont_state[6] = 90		# open
		elif joy.b > 0:
			self.cont_state[6] = 0		# closed

	def get_state(self):
		# base
		self.state[0] = self.steppers[0].state
		self.state[1] = self.steppers[1].state

		# mid-arm
		self.state[2] = self.steppers[2].state
		self.state[3] = self.servos.servo[0].angle

		# wrist
		self.state[4] = self.steppers[3].state
		self.state[5] = self.servos.servo[1].angle

		# end-of-arm tool
		self.state[6] = self.servos.servo[2].angle

	def update(self):
		# update self.target
		self.target[0] += self.cont_state[0]
		self.target[1] += self.cont_state[1]
		self.target[2] += self.cont_state[2]
		self.target[3] += self.cont_state[3]
		self.target[4] += self.cont_state[4]
		self.target[5] += self.cont_state[5]
		self.target[6] = self.cont_state[6]

		# set new stepper positions
		self.steppers[0].update(self.target[0])
		self.steppers[1].update(self.target[1])
		self.steppers[2].update(self.target[2])
		self.steppers[3].update(self.target[4])

		# set new servo positions
		try:
			self.servos.servo[0].angle = self.target[3]			# joint 4
			self.servos.servo[1].angle = self.target[5]			# joint 6
			self.servos.servo[2].angle = self.target[6]			# tooling
		except:
			pass				# angle probably out of range

	def print_state(self):
		# print stepper and servo angles
		print(self.cont_state, self.target, self.state, sep=', ')



joy = Controller()

joints = Joints(0, 0, 0, 0, 0, 0)


try:
	while True:
		time.sleep(0.1)

		joints.get_state()
		joints.get_controller_state(joy)
		joints.update()

		print(joints.target, end=' | ')
		joints.print_state()


except KeyboardInterrupt:
	print("stopping")
	GPIO.cleanup()
