/*
nano every monitors power for 6-axis robotic arm.
sends shutdown command when battery power is below a threshold
*/

#define BAT_VOLT_PIN A0		/* voltage sensor pin from battery */
#define SPLY_VOLT_PIN A2	/* voltage sensor pin from power supply */
#define BTN_PIN A4			/* on button pin for turn-off signal */

#define TOPI_PIN 2			/* signal to raspberry pi to shutdown or not */
#define TOBAT_PIN 4			/* signal to keep battery connected to system */

#define BAT_OFF_THRSH 100	/* 0 - 255? shutdown below this reading */
#define BAT_LOW_THRSH 120	/* 0 - 255? indicate low battery below this reading */

int btn_released = 0;		/* start listening for turn-off signal when button is released from turn-on signal */

void shutdown() {
	digitalWrite(TOPI_PIN, LOW);		/* tell raspberry pi its over */
	delay(1);							/* give raspberry pi time to shutdown gracefully */
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
	/* check if button is released from turn-on signal */
	if (btn_released == 0 && digitalRead(BTN_PIN) == LOW) btn_released = 1;

	/* check if battery voltage below threshold if power supply isnt running */
	if (analogRead(BAT_VOLT_PIN) < BAT_THRSH &&
		digitalRead(SPLY_VOLT_PIN) == LOW) {

		shutdown();
	}

	/* check turn-off signal */
	if (btn_released == 1 && digitalRead(BTN_PIN) == HIGH) shutdown();

	Serial.print(analogRead(BAT_VOLT_PIN));
	Serial.print(" ");
	Serial.println(analogRead(SPLY_VOLT_PIN));

	delay(1);
}
