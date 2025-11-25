/*
nano every monitors power for 6-axis robotic arm.
sends shutdown command when battery power is below a threshold
*/
#include <FastLED.h>


#define BAT_VOLT_PIN A4		/* voltage sensor pin from battery */
#define SPLY_VOLT_PIN A2	/* voltage sensor pin from power supply */
#define BTN_PIN A0			/* on button pin for turn-off signal */

#define TOPI_PIN 2			/* signal to raspberry pi to shutdown or not */
#define TOBAT_PIN 4			/* signal to keep battery connected to system */

#define BAT_OFF_THRSH 400	/* 0 - 1023? shutdown below this reading */
#define BAT_LOW_THRSH 450	/* 0 - 1023? indicate low battery below this reading */

#define GP_START 2000		/* grace period after which arduino will start checking battery voltage */

#define LED_DATA_PIN 12
#define NUM_LEDS 60			/* number of leds in one strip */

int btn_released = 0;		/* start listening for turn-off signal when button is released from turn-on signal */

void shutdown() {
	Serial.println("shutdown started");
	digitalWrite(TOPI_PIN, LOW);		/* tell raspberry pi its over */
	delay(3000);						/* give raspberry pi time to shutdown gracefully */
	digitalWrite(TOBAT_PIN, LOW);		/* kills system */
}

void setup() {
	/* setup serial */
	Serial.begin(9600);

	/* setup pins */
	pinMode(BAT_VOLT_PIN, INPUT);
	pinMode(SPLY_VOLT_PIN, INPUT);
	pinMode(BTN_PIN, INPUT);

	pinMode(TOPI_PIN, OUTPUT);
	pinMode(TOBAT_PIN, OUTPUT);

	digitalWrite(TOPI_PIN, HIGH);
	digitalWrite(TOBAT_PIN, HIGH);
}

void loop() {
	int btn = digitalRead(BTN_PIN);
	int bat_volt = analogRead(BAT_VOLT_PIN);
	int psu_volt = analogRead(SPLY_VOLT_PIN);

	/* check if button is released from turn-on signal */
	if (btn_released == 0 && btn == LOW) btn_released = 1;

	/* check if battery voltage below threshold and power supply isnt running */
	if (bat_volt < BAT_OFF_THRSH && psu_volt < 50 && millis() > GP_START) {

		Serial.println("battery voltage too low");
		shutdown();
	}

	/* check turn-off signal */
	if (btn_released == 1 && btn == HIGH) shutdown();

	Serial.print("battery voltage: ");
	Serial.print(bat_volt);
	Serial.print("\tpsu voltage: ");
	Serial.println(psu_volt);

	delay(100);
}
