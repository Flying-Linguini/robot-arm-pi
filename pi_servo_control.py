from adafruit_servokit import ServoKit		# works with PCA9685 servo controller
from inputs import get_gamepad
import math
import time
import threading
from RPi import GPIO
from subprocess import call
import serial

print("starting")

working = True				# false when program stops

CTR_BASE_ANGLE = 135		# encoder reading when arm base faces straight forward

# io layout of raspberry pi's is dumb. the stepper pins take up the end of the headers opposite the power pins

SHTDWN_PIN = 22 			# signal from arduino (0 for shutdown command, 1 otherwise)

LEFT_QR_PIN = 23			# pins for restricting movement different sides
RIGHT_QR_PIN = 24

#ENC1_PIN = 12				# encoder pin for joint 1
#ENC2_PIN = 16
#ENC3_PIN = 20
#ENC5_PIN = 21				# skips joint 4 (just for steppers)

DIR1_PIN = 6
DIR2_PIN = 13
DIR3_PIN = 19
DIR5_PIN = 26

STEP1_PIN = 25
STEP2_PIN = 8
STEP3_PIN = 7
STEP5_PIN = 1

CW = 1
CCW = 0
STEPS_PER_REV = 200			# for steppers
STEP_DELAY = 0.0005 / 1		# found experimentally. seems to sork pretty well (divided by resolution)

STEP_MODE = (10, 9, 11)		# same for all steppers for now
RESOLUTION = {'full': (0, 0, 0),
			'half': (1, 0, 0),
			'1/4': (0, 1, 0),
			'1/8': (1, 1, 0),
			'1/16': (0, 0, 1),
			'1/32': (1, 0, 1)}

GPIO.setmode(GPIO.BCM)

GPIO.setup(SHTDWN_PIN, GPIO.IN)
GPIO.setup(LEFT_QR_PIN, GPIO.IN)
GPIO.setup(RIGHT_QR_PIN, GPIO.IN)

GPIO.setup(DIR1_PIN, GPIO.OUT)
GPIO.setup(DIR2_PIN, GPIO.OUT)
GPIO.setup(DIR3_PIN, GPIO.OUT)
GPIO.setup(DIR5_PIN, GPIO.OUT)
GPIO.setup(STEP1_PIN, GPIO.OUT)
GPIO.setup(STEP2_PIN, GPIO.OUT)
GPIO.setup(STEP3_PIN, GPIO.OUT)
GPIO.setup(STEP5_PIN, GPIO.OUT)
#GPIO.setup(ENC1_PIN, GPIO.IN)
#GPIO.setup(ENC2_PIN, GPIO.IN)
#GPIO.setup(ENC3_PIN, GPIO.IN)
#GPIO.setup(ENC5_PIN, GPIO.IN)

GPIO.setup(STEP_MODE, GPIO.OUT)
GPIO.output(STEP_MODE, RESOLUTION['full'])

encs = [0, 0, 0, 0]				# encoder values from serial


def _read_encoders():
	global working, encs

	raw = [0, 0, 0, 0]

	ser = serial.Serial("/dev/ttyACM0", 115200, timeout=1)		# check usb device name

	while working:
		line = ser.readline().decode("utf-8", errors="ignore").strip()
		if not line:
			continue

		try:
			raw[0], raw[1], raw[2], raw[3] = line.split(',')

			encs = [int(raw[0]), int(raw[1]), int(raw[2]), int(raw[3])]

		except ValueError:
			# line probably malformed
			continue

		time.sleep(0.001)

# serial monitoring has its own thread
_enc_monitoring = threading.Thread(target = _read_encoders, args = ())
_enc_monitoring.daemon = True
_enc_monitoring.start()



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
		global working

		# joystick deadzone from center
		JOY_DZ = 1000

		while working:
			try:
				events = get_gamepad()
			except:
				# probably no controller connected
				print("no controller connected...")

				time.sleep(1)
				continue

			for event in events:
				#print(f"Event type: {event.ev_type}, Code: {event.code}, State: {event.state}")

				match event.code:
					# joysticks
					case "ABS_X":
						if abs(event.state) > JOY_DZ:
							self.left_joy_x = event.state
						else:
							self.left_joy_x = 0

					case "ABS_Y":
						if abs(event.state) > JOY_DZ:
							self.left_joy_y = event.state
						else:
							self.left_joy_y = 0

					case "BTN_THUMBL":
						self.left_thumb = event.state

					case "ABS_RX":
						if abs(event.state) > JOY_DZ:
							self.right_joy_x = event.state
						else:
							self.right_joy_x = 0

					case "ABS_RY":
						if abs(event.state) > JOY_DZ:
							self.right_joy_y = event.state
						else:
							self.right_joy_y = 0

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
					case "ABS_LZ":
						self.left_trig = event.state
					case "ABS_RZ":
						self.right_trig = event.state

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



joy = Controller()



class StepperDriver():
	# handles one stepper motor each instance. this must be handled on main thread for GPIO allocation reasons
	def __init__(self, dir_pin, step_pin, enc_idx, precision):
		global CW

		self.dir_pin = dir_pin
		self.step_pin = step_pin
		self.enc_idx = enc_idx
		self.precision = precision 			# motor stops moving when within precision of target

		self.state = 0						# initial state
		self.target = 0

		self.step_state = 0					# 1 or 0 for stepping high or low (> 0 for waiting)

		GPIO.output(self.dir_pin, CW)		# initial direction

	def get_state(self):
		# get encoder state from serial
		global encs
		# readings go from ~-300 to ~300
		self.state = (encs[self.enc_idx] + 300) * 0.45		# translate readings to degrees

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

	def step(self):
		if abs(self.state - self.target) > self.precision:
			if self.step_state == 0:
				# go high
				GPIO.output(self.step_pin, GPIO.HIGH)
				self.step_state = 1

			elif self.step_state == 1:
				# go low
				GPIO.output(self.step_pin, GPIO.LOW)
				self.step_state = -1

			elif self.step_state == -1:
				# wait to limit speed
				self.state_state = 0



class Joints():
	def __init__(self):
		global DIR1_PIN, DIR2_PIN, DIR3_PIN, DIR5_PIN
		global STEP1_PIN, STEP2_PIN, STEP3_PIN, STEP5_PIN
		global ENC1_PIN, ENC2_PIN, ENC3_PIN, ENC5_PIN

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
		time.sleep(0.01)
		self.steppers.append(StepperDriver(DIR1_PIN, STEP1_PIN, 0, 5))
		time.sleep(0.01)
		self.steppers.append(StepperDriver(DIR2_PIN, STEP2_PIN, 1, 5))
		time.sleep(0.01)
		self.steppers.append(StepperDriver(DIR3_PIN, STEP3_PIN, 2, 5))
		time.sleep(0.01)
		self.steppers.append(StepperDriver(DIR5_PIN, STEP5_PIN, 3, 5))

		# thread stuff
		self._handle_thread = threading.Thread(target = self._handle_joints, args = ())
		self._handle_thread.daemon = True
		self._handle_thread.start()

	def get_controller_state(self, joy):
		# base
		self.cont_state[0] = joy.left_joy_x / 32767
		self.cont_state[1] = joy.left_joy_y / 32767

		# mid-arm
		self.cont_state[2] = joy.right_joy_y / 32767
		self.cont_state[3] = joy.right_joy_x / 32767

		# wrist
		if joy.right_trig > 0:
			self.cont_state[4] = joy.right_trig
		else:
			self.cont_state[4] = -joy.left_trig

		if joy.right_bump > 0:
			self.cont_state[5] = joy.right_bump
		else:
			self.cont_state[5] = -joy.left_bump

		# tooling
		if joy.a > 0:
			self.cont_state[6] = 170	# open
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
		global LEFT_QR_PIN, RIGHT_QR_PIN, CTR_BASE_ANGLE

		# update self.target
		self.target[0] += self.cont_state[0]
		self.target[1] += self.cont_state[1]
		self.target[2] += self.cont_state[2]
		self.target[3] += self.cont_state[3]
		self.target[4] += self.cont_state[4]
		self.target[5] += self.cont_state[5]
		self.target[6] = self.cont_state[6]

		# set new stepper positions
		# base checks for restrictions
		#if self.target[0] < CTR_BASE_ANGLE and GPIO.input(RIGHT_QR_PIN) == GPIO.LOW:
		self.steppers[0].update(self.target[0])
		#elif self.target[0] < CTR_BASE_ANGLE and GPIO.input(RIGHT_QR_PIN) == GPIO.HIGH:
		#	self.steppers[0].update(CTR_BASE_ANGLE)

		#if self.target[0] > CTR_BASE_ANGLE and GPIO.input(LEFT_QR_PIN) == GPIO.LOW:
		self.steppers[0].update(self.target[0])
		#elif self.target[0] > CTR_BASE_ANGLE and GPIO.input(LEFT_QR_PIN) == GPIO.HIGH:
		#	self.steppers[0].update(CTR_BASE_ANGLE)

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

	def _handle_joints(self):
		global working, joy

		# initialize
		time.sleep(1)		# give encoders time to average out true
		self.get_state()
		self.target[0] = self.state[0]
		self.target[1] = self.state[1]
		self.target[2] = self.state[2]
		self.target[3] = self.state[3]
		self.target[4] = self.state[4]
		self.target[5] = self.state[5]
		self.target[6] = self.state[6]

		while working:
			self.get_state()
			self.get_controller_state(joy)
			self.update()

			time.sleep(0.01)

	def print_state(self):
		# print stepper and servo angles
		print(self.cont_state, self.target, self.state, sep=', ')



joints = Joints()


"""while True:
	for s in joints.steppers:
		#s.check_step()
		s.step()

	time.sleep(STEP_DELAY)"""


now = time.time()

try:
	while working:
		then = now
		now = time.time()

		# ensure proper timing for steppers
		while now - then < STEP_DELAY:
			time.sleep(0.00001)
			now = time.time()

		#print((now - then))

		# step steppers
		for s in joints.steppers:
			s.check_step()
			s.step()

		# print stuff
		#print(joints.target, end='\t|\t')
		joints.print_state()
		print(encs)

		# check for shutdown
		if GPIO.input(SHTDWN_PIN) == GPIO.LOW:
			GPIO.cleanup()
			call("shutdown now", shell=True)

except KeyboardInterrupt:
	print("stopping")

GPIO.cleanup()
