from PyQt5 import QtWidgets, QtGui, QtCore
import sys
import GUI
# use the py file name you coverted using pyuic
from PyQt5.QtWidgets import QMessageBox
from paho.mqtt import client as mqtt_client

broker = 'broker.emqx.io'
# broker = '10.64.98.135'
port = 1883
UItoRpi = "UItoRpi"
RpitoUI = "RpitoUI"
client_id = "UI"


class MainWindow(QtWidgets.QMainWindow, GUI.Ui_MainWindow):
    """UI Window class"""
    # Create client and make sure it is connected
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to Broker successfully !")
        else:
            print("Failed to connect", rc)

    client = mqtt_client.Client(client_id)

    client.on_connect = on_connect
    client.connect(broker, port)

    def __init__(self):
        """Initialize the window class"""
        super(MainWindow, self).__init__()
        self.setupUi(self)

        # initially disable checkboxes for all parking slots
        self.Slot1.setEnabled(False)
        self.Slot2.setEnabled(False)
        self.Slot3.setEnabled(False)
        self.Slot4.setEnabled(False)
        self.Slot5.setEnabled(False)

        # Create On/Off for warning light and Send button for sending message
        self.AlertOff.clicked.connect(self.emergency_off)
        self.AlertOn.clicked.connect(self.emergency_on)
        self.SendMsg.clicked.connect(self.getMsg)

    # this function all required data on the UI, this data include car position, parking request, and sensor data
    def display_UI(self, position, request, sensor):

        x = {'slot1': self.Slot1, 'slot2': self.Slot2,
             'slot3': self.Slot3, 'slot4': self.Slot4, 'slot5': self.Slot5}
        # Car request to park into the slot
        if (request == "in "):
            if (x[position].isChecked() == True):  # if the slot is occupied
                print("this slot is already occupied, park somewhere else ")
            else:  # if not, check the box of that spot
                x[position].setChecked(True)
                print("Car just got in parking", position)
        # Car request to get out of the slot
        if (request == "out"):
            # if the slot is occupied, uncheck the check box of that slot
            if (x[position].isChecked() == True):
                x[position].setChecked(False)
                print("Car just got out of parking", position)
            else:  # if not
                print('No car at parking', position)
        # if there is no parking request
        if (request == "off"):
            # change the color of the check box where the car is currently at to pin point its current location, the rest keep of
            # the check boxes keep their color
            x[position].setStyleSheet("background-color: white")
            if (position != "slot1"):
                x["slot1"].setStyleSheet("background-color: yellow")
            if (position != "slot2"):
                x["slot2"].setStyleSheet("background-color: yellow")
            if (position != "slot3"):
                x["slot3"].setStyleSheet("background-color: yellow")
            if (position != "slot4"):
                x["slot4"].setStyleSheet("background-color: yellow")
            if (position != "slot5"):
                x["slot5"].setStyleSheet("background-color: yellow")
            print("Car is at parking", position)
        # Display sensor data on the sensor lable on the UI
        self.SensorDisplay.setText(sensor)

    # subscribe the message from the broker which contains teh car's position, parking request and temperature sensor data
    def subscribe(self, client: mqtt_client):
        def on_message(client, userdata, msg):
            message = msg.payload.decode()
            # spliting the subscription message into catagories
            message_list = message.split(",")
            request = message_list[0]
            position = message_list[1]
            sensor_data = message_list[2]

            print("***********************SUBSCRIPTION*************************")
            # display the data on the UI by calling display_UI function
            self.display_UI(position, request, sensor_data)

        client.subscribe(RpitoUI)
        client.on_message = on_message

    # This funcition take in message as parameter and publish that message to the broker
    def publish(self, client, msg):
        client.publish(UItoRpi, msg)
        print("***********************PUBLISHION*************************")
        print("Message:", msg, "sent!")

    # This function is called everytime the warning off button is pressed, which will publish the message to ask raspberry pi to turn
    # off waring light
    def emergency_off(self):
        msg = 'Emergency Off'
        self.publish(self.client, msg)

    # This function is called everytime the warning on button is pressed, which will publish the message to ask raspberry pi to turn
    # on waring light
    def emergency_on(self):
        msg = 'Emergency On'
        self.publish(self.client, msg)

    # This function is called everytime the send message is pressed, which will send the user input message to the display board
    def getMsg(self):
        # store the message from message box to variable
        message = self.MsgBox.toPlainText()
        # then clear the message box
        self.MsgBox.clear()
        self.publish(self.client, message)

    def run(self):

        self.client.loop_start()
        self.subscribe(self.client)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.run()
    mainWindow.show()
    sys.exit(app.exec_())
