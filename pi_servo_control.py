import gpiozero as gpz
import time

print("starting")

servo = gpz.Servo(25)			# servo wired to pin 25

val = -1						# servo positions range from -1 to 1

try:
	while True:
		servo.value = val

		time.sleep(0.1)

		val += 0.1

		if val > 1:
			val = -1

		print("val: %3.1f", val)

except KeyboardInterrupt:
	print("stopping")
