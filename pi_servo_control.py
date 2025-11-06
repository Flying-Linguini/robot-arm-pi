from adafruit_servokit import ServoKit		# works with PCA9685 servo controller
from inputs import get_gamepad
import math
import time
import threading

print("starting")

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


class Joints():
	def __init__(self, pin1, pin2, pin3, pin4, pin5, pin6):
		self.target = [0, 0, 0, 0, 0, 0]		# target angles of all joints

		#self.servo = gpz.Servo(pin)
		self.servos = ServoKit(channels=16)		# for joints 4, 5, and 6

		self.servos.frequency = 60

		self.servos.servo[0].set_pulse_width_range(1000, 2000)
		self.servos.servo[1].set_pulse_width_range(1000, 2000)
		self.servos.servo[2].set_pulse_width_range(1000, 2000)

	def update(self):
		# set new servo positions
		try:
			self.servos.servo[0].angle = self.target[3];		# joint 4
			self.servos.servo[1].angle = self.target[4];		# joint 5
			self.servos.servo[2].angle = self.target[5];		# joint 6
		except:
			pass				# angle probably out of range

	def print_state(self):
		# print stepper and servo angles
		print(self.servos.servo[0].angle, self.servos.servo[1].angle, self.servos.servo[2].angle, sep=', ')


#servo = gpz.Servo(25)			# servo wired to pin 25

#val = -1						# servo positions range from -1 to 1

joy = Controller()

joints = Joints(0, 0, 0, 0, 0, 0)

try:
	while True:
		time.sleep(1)

		joints.target[3] = 0
		joints.target[4] = 0
		joints.target[5] = 0

		joints.update()

		print(joints.target, end=' | ')
		joints.print_state()

		time.sleep(1)

		joints.target[3] = 179
		joints.target[4] = 179
		joints.target[5] = 179

		joints.update()

		print(joints.target, end=' | ')
		joints.print_state()

except KeyboardInterrupt:
	print("stopping")
