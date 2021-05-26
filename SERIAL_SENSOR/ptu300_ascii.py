import serial
import os
import re
import json
import logging
import warnings
import value_checks
from threading import Timer


class PTU300ascii:

    def __init__(self, client, mqtt_topic, qos, port, baud):
        self.serial_port = serial.Serial(port, baud, timeout=1.0)
        logging.info('Serial port: ' + str(self.serial_port))

        # b"P=  1003.8 hPa   T= 17.7 'C RH= 40.9 %RH TD=  4.3 'C  trend=*****
        # tend=*\r\n"
        self.ptu300search = re.compile('P=.+hPa.+T=.+RH=.+TD=.+trend=.+tend=.')
        self.client = client
        self.mqtt_topic = mqtt_topic
        self.qos = qos
        self.serial_port_reader()

    def serial_port_reader(self):
        """Read a line of incoming data from the assigned serial port, then
        pass the data onto a processor for extraction of the data values"""
        try:
            data_bytes = self.serial_port.readline()
            dataline = str(data_bytes)
            # Only process output if we have actual data in the line
            if len(dataline) > 30:
                logging.info(
                    'RAW data: ' + str(self.serial_port.name) + ' ' + dataline)
                data_elements = self.data_decoder(dataline)
                data = get_readings(data_elements)[0]
                self.client.publish(self.mqtt_topic, json.dumps(data),
                                    self.qos)
                logging.info(
                    'Published topic:' + self.mqtt_topic + ' ' + str(data))
        except serial.SerialException as error:
            warnings.warn("Serial port error: " + str(error), Warning)
        # Asynchronously schedule this function to be run again in 1.0 seconds
        Timer(1, self.serial_port_reader).start()

    def data_decoder(self, dataline):
        """
        Extract available weather parameters from the sensor data, check that
        data falls within sensible boundaries. if necessary, the sensor must
        be setup to output its data in the required format e.g.
        P=  1003.8 hPa   T= 17.4 'C RH= 41.3 %RH " TD= 4.2 'C  trend=-0.4
        tend=7
        with units of hPa, degrees C and % humidity.
        :param dataline: Sensor data output string.
        """
        pressure = None
        humidity = None
        temperature = None
        dew_point = None

        if self.ptu300search.search(dataline):
            """ Apply any instrument corrections """
            pressure_correction = float(os.getenv('PRESS_CORR', 0.0))
            temperature_correction = float(os.getenv('TEMP_CORR', 0.0))
            humidity_correction = float(os.getenv('HUMI_CORR', 0.0))

            """Check we have PTU300 data available and then extract 
            numeric values from this data """
            data = find_numeric_data(dataline)
            if 3 < len(data) < 7:
                if value_checks.pressure_check(float(data[0])):
                    pressure = float(data[0]) + pressure_correction
                if value_checks.temperature_check(float(data[1])):
                    temperature = float(data[1]) + temperature_correction
                if value_checks.humidity_check(int(round(float(data[2])))):
                    humidity = int(
                        round(float(data[2]) + humidity_correction, 0))
                if value_checks.temperature_check(float(data[3])):
                    dew_point = float(data[3])

                # This sensor can output e.g. 102% humidity which is
                # probably correct (supersaturation) but not accepted by
                # e.g. weather underground map display data.
                if humidity > 100:
                    humidity = 100
            else:
                warnings.warn('invalid PTU300 data', Warning)

            return pressure, temperature, dew_point, humidity


def get_readings(data_elements):
    """
    Return the latest recorded values from the instrument
    :return: Formatted instrument readings list
    """
    if data_elements is not None:
        return [
            {
                'pressure': data_elements[0],
                'temperature': data_elements[1],
                'dew_point': data_elements[2],
                'humidity': data_elements[3],
            }
        ]
    else:
        return [
            {
                'pressure': None,
                'temperature': None,
                'dew_point': None,
                'humidity': None,
            }
        ]


def find_numeric_data(dataline):
    """Use regular expressions to find and extract all digit data groups.
    This will include values like 1, 12.3, 2345, 0.34 i.e. any number or
    decimal number.
    :param dataline: The data line from digit groups are to be extracted.
    :return: A list containing the digit groups extracted.
    """
    data_search_exp = '[-+]? (?: (?: \d* \. \d+ ) | (?: \d+ \.? ' \
                      ') )(?:' \
                      '[Ee] [+-]? \d+ ) ?'

    find_data_exp = re.compile(data_search_exp, re.VERBOSE)
    data = find_data_exp.findall(dataline)
    return data
