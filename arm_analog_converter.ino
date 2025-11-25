/* arduino nano code used to convert analog signals from encoders to serial for the raspberry pi */

#define ENC1_PIN A1
#define ENC2_PIN A2
#define ENC3_PIN A3
#define ENC4_PIN A4

int base[75];
int shoulder[75];
int elbow[75];
int wrist[75];

int idx = 0;		/* write index for averages */

int average(int *data, int len) {
	/* average values from list of ints */
	int i;
	int sum = 0;

	for (i = 0; i < len; i++) {
		sum = sum + data[i];
	}

	return sum / len;
}


void setup() {
	/* setup serial */
	Serial.begin(115200);

	/* setup pins */
	pinMode(ENC1_PIN, INPUT);
	pinMode(ENC2_PIN, INPUT);
	pinMode(ENC3_PIN, INPUT);
	pinMode(ENC4_PIN, INPUT);
}

void loop() {
	/* update idx */
	if (idx > 74) idx = 0;
	else idx++;

	base[idx] = analogRead(ENC1_PIN);
	shoulder[idx] = analogRead(ENC2_PIN);
	elbow[idx] = analogRead(ENC3_PIN);
	wrist[idx] = analogRead(ENC4_PIN);

	Serial.print(average(base, 100));
	Serial.print(",");
	Serial.print(average(shoulder, 100));
	Serial.print(",");
	Serial.print(average(elbow, 100));
	Serial.print(",");
	Serial.println(average(wrist, 100));

	delay(10);
}
