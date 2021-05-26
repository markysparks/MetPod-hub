#!/usr/bin/python3
import math
from threading import Timer


class WindProcessor:
    """Functions for calculating 10 minute and 2 minute mean wind values.
    Note that though both methods use duplicate code they have been kept
    separate for the sake of clarity. Wind speed and direction u and v
    vector component values are stored in lists until the appropriate time
    flag has been set to True. The arctan function is then used to convert
    back to wind direction and speed. This method takes account of the
    magnitude of wind vectors when calculating a mean. As a new input is
    received the oldest reading is discarding thereby ensuring a 'rolling
    mean'. Finally the output is formatted according to meteorological
    convention. """

    def __init__(self, flag2min=False, flag10min=False):
        self.flag2min = flag2min
        self.flag10min = flag10min
        self.wind_gust_10min = None
        self.wind_speed_max_10min = None
        self.wind_speed_min_10min = None
        self.wind_speed_max_2min = None
        self.wind_speed_min_2min = None
        self.mean_wind_dir_10min = None
        self.mean_wind_speed_10min = None
        self.wind_gust_2min = None
        self.mean_wind_dir_2min = None
        self.mean_wind_speed_2min = None
        self.wind_speeds_10min = []
        self.wind_dirs_10min = []
        self.v_components10min = []
        self.u_components10min = []
        self.wind_speeds_2min = []
        self.wind_dirs_2min = []
        self.v_components2min = []
        self.u_components2min = []
        # # Setup scheduler for 10 minute wind calculations
        # scheduler = BackgroundScheduler()
        # scheduler.add_job(
        #     self.set_10min_flag, IntervalTrigger(minutes=10))
        #
        # # setup scheduler for 2 minute wind calculations
        # scheduler.add_job(
        #     self.set_2min_flag, IntervalTrigger(minutes=2))
        # scheduler.start()

        Timer(180, self.set_2min_flag).start()
        Timer(600, self.set_10min_flag).start()

    def set_10min_flag(self):
        """Set the 10 min flag to True when 10 minutes have elapsed
        since startup."""
        self.flag10min = True

    def set_2min_flag(self):
        """Set the 2 min flag to True when 2 minutes have elapsed
        since startup."""
        self.flag2min = True

    def process_wind_10min(self, winddir, windspeed):
        """Process wind and direction inputs into the 10 minute averaging
        mechanism.
        :param winddir: The instantaneous wind direction in degrees.
        :param windspeed: The instantaneous wind speed in knots.
        :return: A list containing he 10 minute mean wind direction,
        speed and max gust. Values will be None if the 10 minutes have not
        elapsed since startup.
        """
        if winddir is None or windspeed is None:
            self.flag10min = False
            self.wind_gust_10min = None
            self.mean_wind_dir_10min = None
            self.mean_wind_speed_10min = None

        elif self.flag10min is False:
            self.wind_dirs_10min.append(winddir)
            self.wind_speeds_10min.append(windspeed)
            self.u_components10min.append(
                (-1 * (windspeed * math.sin(winddir * math.pi / 180))))
            self.v_components10min.append(
                (-1 * (windspeed * math.cos(winddir * math.pi / 180))))
            self.wind_gust_10min = None

        else:
            try:
                self.wind_speed_min_10min = min(self.wind_speeds_10min)

                self.wind_dirs_10min.append(winddir)
                self.wind_dirs_10min.pop(0)

                self.wind_speeds_10min.append(windspeed)
                self.wind_speeds_10min.pop(0)

                self.u_components10min.append(
                    (-1 * (windspeed * math.sin(winddir * math.pi / 180))))
                self.u_components10min.pop(0)

                self.v_components10min.append(
                    (-1 * (windspeed * math.cos(winddir * math.pi / 180))))
                self.v_components10min.pop(0)

                windspeeds_sum_10min = sum(self.wind_speeds_10min)
                u_comps_sum_10min = sum(self.u_components10min)
                v_comps_sum_10min = sum(self.v_components10min)

                u_comp_mean_10min = u_comps_sum_10min / len(
                    self.u_components10min)
                v_comp_mean_10min = v_comps_sum_10min / len(
                    self.v_components10min)

                self.wind_gust_10min = max(self.wind_speeds_10min)
                self.wind_speed_min_10min = min(self.wind_speeds_10min)
                self.wind_speed_max_10min = self.wind_gust_10min

                if u_comp_mean_10min > 0:
                    self.mean_wind_dir_10min = int(round(
                        90 - 180 / math.pi * math.atan(
                            v_comp_mean_10min / u_comp_mean_10min) + 180))

                elif u_comp_mean_10min < 0:
                    self.mean_wind_dir_10min = int(round(
                        90 - 180 / math.pi * math.atan(
                            v_comp_mean_10min / u_comp_mean_10min)))

                elif u_comp_mean_10min == 0:

                    if v_comp_mean_10min < 0:
                        self.mean_wind_dir_10min = 360

                    elif v_comp_mean_10min > 0:
                        self.mean_wind_dir_10min = 180

                    else:
                        self.mean_wind_dir_10min = 0

                self.mean_wind_speed_10min = int(
                    round(windspeeds_sum_10min / len(self.v_components10min)))

                # if for some reason we get negative wind spd, set spd to zero
                if self.mean_wind_speed_10min < 0:
                    self.mean_wind_speed_10min = 0

                # North wind is 360 deg by convention
                if self.mean_wind_dir_10min == 0 and \
                        self.mean_wind_speed_10min > 0:
                    self.mean_wind_dir_10min = 360

                # Calm wind dir reported as 0 deg by convention < 2 kts = calm
                if self.mean_wind_speed_10min < 2:
                    self.mean_wind_dir_10min = 0
                    self.mean_wind_speed_10min = 0

                # print('MEAN windDir = ' + str(self.mean_wind_dir_10min))
                # print('MEAN windSpeed = ' + str(self.mean_wind_speed_10min))
                # print('10 MIN GUST = ' + str(self.wind_gust_10min))
            except(ValueError, ZeroDivisionError):
                print('10 min wind flag set but no values for calculation')
                self.wind_dirs_10min.append(winddir)
                self.wind_speeds_10min.append(windspeed)
                self.u_components10min.append(
                    (-1 * (windspeed * math.sin(winddir * math.pi / 180))))
                self.v_components10min.append(
                    (-1 * (windspeed * math.cos(winddir * math.pi / 180))))

        return self.mean_wind_dir_10min, self.mean_wind_speed_10min, \
            self.wind_gust_10min

    def process_wind_2min(self, winddir, windspeed):
        """Process wind and direction inputs into the 2 minute averaging
        mechanism.
        :param winddir: The instantaneous wind direction in degrees.
        :param windspeed: The instantaneous wind speed in knots.
        :return: A list containing the 2 minute mean wind direction,
        speed and max gust. Values will be None if the 2 minutes have not
        elapsed since startup."""
        if winddir is None or windspeed is None:
            self.flag2min = False
            self.wind_gust_2min = None
            self.mean_wind_dir_2min = None
            self.mean_wind_speed_2min = None

        elif self.flag2min is False:
            self.wind_dirs_2min.append(winddir)
            self.wind_speeds_2min.append(windspeed)
            self.u_components2min.append(
                (-1 * (windspeed * math.sin(winddir * math.pi / 180))))
            self.v_components2min.append(
                (-1 * (windspeed * math.cos(winddir * math.pi / 180))))
            # self.windGust2min = max(self.windSpeeds2min)
            self.wind_gust_2min = None

        else:
            try:
                self.wind_speed_min_2min = min(self.wind_speeds_2min)

                self.wind_dirs_2min.append(winddir)
                self.wind_dirs_2min.pop(0)

                self.wind_speeds_2min.append(windspeed)
                self.wind_speeds_2min.pop(0)

                self.u_components2min.append(
                    (-1 * (windspeed * math.sin(winddir * math.pi / 180))))
                self.u_components2min.pop(0)

                self.v_components2min.append(
                    (-1 * (windspeed * math.cos(winddir * math.pi / 180))))
                self.v_components2min.pop(0)

                windspeeds_sum_2min = sum(self.wind_speeds_2min)
                u_comps_sum_2min = sum(self.u_components2min)
                v_comps_sum_2min = sum(self.v_components2min)

                u_comp_mean_2min = u_comps_sum_2min / len(
                    self.u_components2min)
                v_comp_mean_2min = v_comps_sum_2min / len(
                    self.v_components2min)

                self.wind_gust_2min = max(self.wind_speeds_2min)
                self.wind_speed_min_2min = min(self.wind_speeds_2min)
                self.wind_speed_max_2min = self.wind_gust_2min

                if u_comp_mean_2min > 0:
                    self.mean_wind_dir_2min = int(round(
                        90 - 180 / math.pi * math.atan(
                            v_comp_mean_2min / u_comp_mean_2min) + 180))

                elif u_comp_mean_2min < 0:
                    self.mean_wind_dir_2min = int(round(
                        90 - 180 / math.pi * math.atan(
                            v_comp_mean_2min / u_comp_mean_2min)))

                elif u_comp_mean_2min == 0:

                    if v_comp_mean_2min < 0:
                        self.mean_wind_dir_2min = 360

                    elif v_comp_mean_2min > 0:
                        self.mean_wind_dir_2min = 180

                    else:
                        self.mean_wind_dir_2min = 0

                self.mean_wind_speed_2min = int(
                    round(windspeeds_sum_2min / len(self.v_components2min)))

                # if for some reason we get negative wind spd, set spd to zero
                if self.mean_wind_speed_2min < 0:
                    self.mean_wind_speed_2min = 0

                # North wind is 360 deg by convention
                if self.mean_wind_dir_2min == 0 and \
                        self.mean_wind_speed_2min > 0:
                    self.mean_wind_dir_2min = 360

                # Calm wind dir reported as 0 deg by convention < 2 kts = calm
                if self.mean_wind_speed_2min < 2:
                    self.mean_wind_dir_2min = 0
                    self.mean_wind_speed_2min = 0

                # print('MEAN 2min windDir = ' + str(self.mean_wind_dir_2min))
                # print('MEAN 2min windSpd =' + str(self.mean_wind_speed_2min))
                # print('2 MIN GUST = ' + str(self.wind_gust_2min))
            except(ValueError, ZeroDivisionError):
                print('2 min wind flag set but no values for calculation')
                self.wind_dirs_2min.append(winddir)
                self.wind_speeds_2min.append(windspeed)
                self.u_components2min.append(
                    (-1 * (windspeed * math.sin(winddir * math.pi / 180))))
                self.v_components2min.append(
                    (-1 * (windspeed * math.cos(winddir * math.pi / 180))))

        return self.mean_wind_dir_2min, self.mean_wind_speed_2min, \
            self.wind_gust_2min
