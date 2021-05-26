import serial
import os
import re
import json
import logging
import warnings
import value_checks
from threading import Timer
from wind_processor import WindProcessor


class WINDSONICascii:

    def __init__(self, client, mqtt_topic, qos, port, baud):
        self.serial_port = serial.Serial(port, baud, timeout=1.0)
        logging.info('Serial port: ' + str(self.serial_port))

        # b'\x02Q,194,000.04,N,00,\x0315\r\n'
        self.windsonic_pattern = re.compile('\w,\d\d\d,\d\d\d.\d\d,\w,\d\d')
        self.client = client
        self.mqtt_topic = mqtt_topic
        self.qos = qos
        self.wind_processor = WindProcessor()

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
        data falls within sensible boundaries. If necessary, the sensor must
        be setup to output its data in the required format e.g.
        '\x02Q,194,005.04,N,00,\x0315' with units in knots and degrees
        (194 degrees and 5.04 kts in this case).
        :param dataline: Sensor data output string.
        """
        winddir = None
        windspeed = None
        windgust = None
        winddir_avg10m = None
        windspeed_avg10m = None

        if self.windsonic_pattern.search(dataline):
            """ Apply any instrument corrections """
            anemo_offset = int(os.getenv('ANEMO_OFFSET', 0))

            """Check we have Windsonic data available and then extract 
            numeric values from this data """
            data = find_numeric_data(dataline)
            if data is not None and 3 < len(data) < 6:
                winddir_raw = int(round(float(data[1]), 0)) + anemo_offset
                if winddir_raw == 0:
                    pass
                elif winddir_raw < 0:
                    winddir_raw += 360
                elif winddir_raw > 360:
                    winddir_raw -= 360
                windspeed_raw = int(round(float(data[2]), 0))
                if value_checks.windspeed_check(windspeed_raw) \
                        and value_checks.winddir_check(winddir_raw):
                    winddir = winddir_raw
                    windspeed = windspeed_raw
                    mean10min = self.wind_processor.process_wind_10min(
                        winddir, windspeed)
                    if self.wind_processor.flag10min:
                        winddir_avg10m = mean10min[0]
                        windspeed_avg10m = mean10min[1]
                        windgust = mean10min[2]
            else:
                warnings.warn('Invalid WINDSONIC data', Warning)

            return winddir, windspeed, windgust, winddir_avg10m, \
                windspeed_avg10m


def get_readings(data_elements):
    """
    Return the latest recorded values from the instrument
    :return: Formatted instrument readings list
    """
    if data_elements is not None:
        return [
            {
                'winddir': data_elements[0],
                'windspd': data_elements[1],
                'windgust': data_elements[2],
                'winddir10m': data_elements[3],
                'windspd10m': data_elements[4],
            }
        ]
    else:
        return [
            {
                'winddir': None,
                'windspd': None,
                'windgust': None,
                'winddir10m': None,
                'windspd10m': None,
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
