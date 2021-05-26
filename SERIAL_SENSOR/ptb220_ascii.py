import serial
import os
import re
import json
import logging
import warnings
import value_checks
from threading import Timer


class PTB220ascii:

    def __init__(self, client, mqtt_topic, qos, port, baud):
        self.serial_port = serial.Serial(port, baud, timeout=1.0)
        logging.info('Serial port: ' + str(self.serial_port))

        # .P.1  1005.75 ***.* * 1005.8 1005.7 1005.7 000.F9
        self.search_exp = re.compile('.P.+')
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

        if self.search_exp.search(dataline):
            """ Apply any instrument corrections """
            pressure_correction = float(os.getenv('PRESS_CORR', 0.0))
            data = find_numeric_data(dataline)
            logging.info('Numeric data: ' + str(data))
            if value_checks.pressure_check(float(data[2])):
                pressure = float(data[2]) + pressure_correction
            else:
                warnings.warn('invalid PTB220 sensor data', Warning)
            return [pressure]


def get_readings(data_elements):
    """
    Return the latest recorded values from the instrument
    :return: Formatted instrument readings list
    """
    if data_elements is not None:
        return [
            {
                'pressure': data_elements[0],
            }
        ]
    else:
        return [
            {
                'pressure': None,
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
