
import PCF8591 as ADC
import RPi.GPIO as GPIO
import math
import time

from paho.mqtt import client as mqtt_client
GPIO.setmode(GPIO.BOARD)

# Declare broker, port, topic and client id
broker = 'broker.emqx.io'
port = 1883
RpitoUI = "RpitoUI"
UItoRpi = "UItoRpi"
client_id = "sender123"


def setup():
    ADC.setup(0x48)					# Setup PCF8591
    global state


# set red, red ,green and blue pins
redPin = 16
greenPin = 18
bluePin = 12
DO = 13
# set pins as outputs and input
GPIO.setup(redPin, GPIO.OUT)
GPIO.setup(bluePin, GPIO.OUT)
GPIO.setup(greenPin, GPIO.OUT)

# function to turn on red LED


def red():
    GPIO.output(redPin, GPIO.LOW)
    GPIO.output(greenPin, GPIO.HIGH)
    GPIO.output(bluePin, GPIO.HIGH)

# function to turn off LED


def off():
    GPIO.output(redPin, GPIO.HIGH)
    GPIO.output(bluePin, GPIO.HIGH)
    GPIO.output(greenPin, GPIO.HIGH)

# This funciton create a client and make connect it to the broker


def connect_mqtt():
    # Check whether the client is connected successfully due to the variable rc
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker Successfully!")
        else:
            print("Failed to connect", rc)
    # Initialize the client
    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

# This funciton converting the analog value of the temperature sensor to actual temperature value in celsius,
# and return the value as string


def get_sensor():
    # sensor
    analogVal = ADC.read(3)
    Vr = 5 * float(analogVal) / 255
    Rt = 10000 * Vr / (5 - Vr)
    temp = 1/(((math.log(Rt / 10000)) / 3950) + (1 / (273.15+25)))
    temp = temp - 273.15
    msg = str(round(temp, 2))+"°C"
    return str(msg)

# this function will create a loop that keep sending measage to the topic every certain time


def publish(client):
    delay = 3  # set the delay between message send to 3s
    i = 0
    r = 2
    counter = 0
    while True:
        # create arrays for car position and parking request
        position = ['slot1', 'slot2', 'slot3', 'slot4', 'slot5']
        request = ['in ', 'out', 'off']
        i = i

        # if joystick is point upward, car is requesting to park into the current parking slot
        if ADC.read(0) <= 30:
            r = 0  # up
        # if joystick is point upward, car is requesting to get out of the current parking slot
        if ADC.read(0) >= 225:
            r = 1  # down
        # if joystick is point left, move car to the parking slot on the left of the current one
        if ADC.read(1) >= 225:  # left
            # if car already reach the entrance of the parking slot(slot 1), move back to the end (slot5)
            if (i < 0):
                i = 4
            else:
                i -= 1
        # if joystick is point right, move car to the parking slot on the right of the current one
        if ADC.read(1) <= 30:  # right
            # if car already reach the end of the parking slot(slot 5), move back to the entrance (slot1)
            if (i > 3):
                i = 0
            else:
                i += 1
            # if there is no input direction to the joy stick, the car stay at the position as it is and does
            # not have any parking request
        if ADC.read(0) - 125 < 15 and ADC.read(0) - 125 > -15 and ADC.read(1) - 125 < 15 and ADC.read(1) - 125 > -15 and ADC.read(2) == 255:
            i = i
            r = 2
        # get temperature sensor data
        sensor_data = get_sensor()
        # Merge the sensor data, parking request and car's position into a message and then publish it
        msg = request[r] + "," + position[i] + "," + sensor_data
        time.sleep(0.3)
        counter += 1
        # publish every 2 seconds to mitigate joystick input delay
        if counter == 6:
            r = 2
            client.publish(RpitoUI, msg)
            print(msg)
            counter = 0

# this function subscribe the message from broker, based on the message it will adjust the warning light
# or print message on the display board


def subscribe(client: mqtt_client):
    print("***********************DISPLAY BOARD*************************")

    def on_message(client, userdata, msg):
        message = msg.payload.decode()
        if (message == "Emergency Off"):
            off()  # turn off warning light
        elif (message == "Emergency On"):
            red()  # turn on warning light
        else:  # if the message is not about the warning light, print it to the display board
            print(message)

    client.subscribe(UItoRpi)
    client.on_message = on_message


def run():
    setup()
    client = connect_mqtt()
    client.loop_start()
    subscribe(client)
    publish(client)


if __name__ == '__main__':
    run()
