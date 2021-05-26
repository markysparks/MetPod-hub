import logging
import os
import time
from rain_gauge import RainGaugeSetup
import paho.mqtt.client as mqtt


def on_connect(mqtt_client, userdata, flags, rc):
    if rc == 0:
        global Connected  # Use global variable
        Connected = True  # Signal connection
    else:
        logging.info("MQTT Connection failed")


def on_message(mqtt_client, userdata, msg):
    pass
    # topic = msg.topic
    # msg_decode = str(msg.payload.decode("utf-8", "ignore"))
    # msg_in = json.loads(msg_decode)  # decode json data


logging.basicConfig(level=logging.DEBUG)
logging.captureWarnings(True)

if os.getenv('ENABLE', 'false') == 'true':
    Connected = False  # global variable for the state of the connection
    time.sleep(15)  # allow time for networking to be established
    client = mqtt.Client("rain-gauge")  # create new instance
    client.on_connect = on_connect  # attach function to callback
    client.on_message = on_message  # attach function to callback
    client.connect(os.getenv('MQTT_BROKER', 'localhost'))  # connect to broker
    client.loop_start()  # start the loop

    while not Connected:  # Wait for connection
        time.sleep(0.1)

    mqtt_topic = os.getenv('MQTT_TOPIC')
    mqtt_qos = int(os.getenv('MQTT_QOS', '1'))

    RainGaugeSetup(client, mqtt_topic, mqtt_qos)

    while True:
        time.sleep(1)
