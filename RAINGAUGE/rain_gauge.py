#!/usr/bin/python3
import os
import time
import json
import logging
from collections import OrderedDict
from rain_rate_calc import BucketTipHandler
import RPi.GPIO as GPIO
from threading import Timer


class RainGaugeSetup:

    def __init__(self, client, mqtt_topic, mqtt_qos):
        logging.basicConfig(level=logging.DEBUG)
        logging.captureWarnings(True)

        # The Raspberry Pi GPIO pin number to which one wire of the tipping
        # bucket rain gauge will be connected. The other wire will be
        # connected to any GND pin.
        self.client = client
        self.mqtt_topic = mqtt_topic
        self.mqtt_qos = mqtt_qos
        self.gpio_pin = int(os.getenv('GPIO_PIN', '13'))
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Units are either mm or inch
        self.units = os.getenv('UNITS', 'mm')

        # Rainfall amount required to tip the bucket (as specified by the
        # tipping bucket manufacturer).
        self.amount_per_tip = float(os.getenv('AMOUNT_PER_TIP', 0.2))

        # The time interval in seconds between data message transmission.
        self.tx_interval = int(os.getenv('TX_INTERVAL', '5'))

        if self.units == 'mm':
            self.units = 'mm/hr'
        elif self.units == 'inch':
            self.units = 'inch/hr'
        else:
            self.units = 'mm/hr'

        self.rain_data = OrderedDict(
            [('rainrate', 0.0), ('raintip', 0.0), ('units', self.units)])

        self.bucket_tip_handler = BucketTipHandler(self.amount_per_tip)

        logging.info('Amount per tip = ' + str(self.amount_per_tip))
        logging.info('Units = ' + str(self.units))
        logging.info('TX Interval = ' + str(self.tx_interval))

        # Tipping bucket gauge connected to GPIO pin on Raspberry Pi.
        # This registers the call back for pin interrupts
        logging.info('Setting up GPIO pin for Tipping Bucket - PIN = ' + str(
            self.gpio_pin))
        GPIO.add_event_detect(self.gpio_pin, GPIO.FALLING,
                              callback=self.rain_tip_event,
                              bouncetime=500)
        self.tx_message()

    def tx_message(self):
        """Collect the latest rainrate message data, produce and transmit
        a JSON formatted message over the serial port. The raintip field
        will show the amount per tip for one message when a tip occurs. This
        could be tracked to record total rainfall."""
        if self.units.upper() == 'INCH/HR':
            rainrate_inch = round((self.bucket_tip_handler.rate / 25.4), 3)
            self.rain_data.update(
                dict(rainrate=rainrate_inch, units=self.units))

        else:
            self.rain_data.update(
                dict(rainrate=self.bucket_tip_handler.rate, units=self.units))
        dataline = json.dumps(self.rain_data)
        logging.info(dataline)
        self.client.publish(self.mqtt_topic, dataline, self.mqtt_qos)
        self.rain_data.update(dict(raintip=0.0))

        # Asynchronously schedule this function to be run again x seconds
        Timer(self.tx_interval, self.tx_message).start()

    def rain_tip_event(self, channel):
        """Handle rain bucket tip, an initial delay and re-check for the
       GPIO pin status is made to avoid false/noise contacts"""
        time.sleep(0.005)
        # First check if the pin status is still low after the 0.005 delay -
        # if it is then we can assume that this is a genuine tip and not
        # an electrical noise tip.
        if GPIO.input(channel) == 0:
            self.bucket_tip_handler.process_bucket_tip()

            if self.units.upper() == 'INCH/HR':
                amount_per_tip_inch = round((self.amount_per_tip / 25.4), 3)
                self.rain_data.update(dict(raintip=amount_per_tip_inch))
            else:
                self.rain_data.update(dict(raintip=self.amount_per_tip))
