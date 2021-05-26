#!/usr/bin/python3
import time
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.schedulers.background import BackgroundScheduler


class BucketTipHandler:
    """
    Functions that control what happens when a bucket tip occurs. This
    involves keeping a record of the number of tips and starting various
    timers used in rainfall rate calculations.
    """

    def __init__(self, amount_per_tip):
        self.bucket_tips_counter = 0
        self.amount_per_tip = float(amount_per_tip)
        self.tips_timer = Timer()
        self.time_since_1_5_threshold_timer = Timer()
        self.time_since_1_5_threshold = 0
        self.tips_time_delta = 0
        self.time_since_last_tip = 0
        self.rate = 0.0
        self.rain_event_scheduler = BackgroundScheduler()

    def process_bucket_tip(self):
        """
        Start, stop and rest various timers once depending on whether or not
        this is the first or subsequent bucket tip. Provides a mechanism
        to record the time between tips used for rainfall rate calculation.

        A scheduled job is also setup to update the rainfall rate between
        bucket tips every 5 seconds. This allows for the e.g. rate to be
        reduced as the time since the last tip increases.
        """

        # Initial setup of rate update scheduler.
        if self.rain_event_scheduler.running:
            self.rain_event_scheduler.remove_all_jobs()
            self.rain_event_scheduler.add_job(self.update_rain_rate,
                                              IntervalTrigger(seconds=5))
            self.rain_event_scheduler.resume()
        # Subsequently for subsequent rain events the scheduler will be paused
        # so needs to have 'update rate job' added back in and resumed.
        else:
            self.rain_event_scheduler.add_job(self.update_rain_rate,
                                              IntervalTrigger(seconds=5))
            self.rain_event_scheduler.start()

        self.bucket_tips_counter += 1

        # First tip of rainfall event.
        if self.bucket_tips_counter == 1:
            self.tips_timer.start()
            self.rate = self.rain_rate_calc(self.bucket_tips_counter,
                                            self.amount_per_tip)

        # Second and subsequent tips, we can obtain a time delta between tips.
        else:
            # self.bucket_tips_counter == 2
            self.tips_time_delta = self.elapsed_time_between_tips()
            self.rate = self.rain_rate_calc(self.bucket_tips_counter,
                                            self.amount_per_tip,
                                            self.tips_time_delta)

    def update_rain_rate(self):
        """Update the rain rate based on the elapsed time since the last bucket
        tip. The time since the last tip is checked  and the new rate
        calculated based on this time, either the rate will be kept the same,
        reduced or rain assumed stopped. See the rate calculation function
        for more details of the calculation"""
        elapsed_time_last_tip = self.elapsed_time_since_last_tip()
        # No tip for for 60 mins - rain event ended so reset (60 * 60).
        if elapsed_time_last_tip > 3600:
            print('60 min End of rain event - no tip')
            self.end_of_rain_event_reset()
        else:
            if elapsed_time_last_tip >= (1.5 * self.tips_time_delta) and not \
                    self.time_since_1_5_threshold_timer.running and \
                    self.bucket_tips_counter > 1:
                self.time_since_1_5_threshold_timer.start()

            self.rate = self.rain_rate_calc(self.bucket_tips_counter,
                                            self.amount_per_tip,
                                            self.tips_time_delta,
                                            elapsed_time_last_tip,
                                            self.elapsed_time_1_5_threshold())
            if self.rate == 0.0:
                self.end_of_rain_event_reset()

    def elapsed_time_between_tips(self):
        """Return the elapsed time between the last two tips
        :return: The elapsed time between the last two bucket tips.
        """
        self.tips_timer.stop()
        elapsed_time = self.tips_timer.elapsed
        self.tips_timer.reset()
        self.tips_timer.start()
        return elapsed_time

    def elapsed_time_since_last_tip(self):
        """Return the elapsed time since the last tip occurred.
        :return: The elapsed time since the last tip occurred.
        """
        self.tips_timer.stop()
        elapsed_time = self.tips_timer.elapsed
        self.tips_timer.start()
        return elapsed_time

    def elapsed_time_1_5_threshold(self):
        """Return the elapsed time since the (time since last tip <
        1.5 * gap between last two tips) threshold reached.
        :return: Elapsed time since the 1.5 threshold.
        """
        if self.time_since_1_5_threshold_timer.running:
            self.time_since_1_5_threshold_timer.stop()
            elapsed_time = self.time_since_1_5_threshold_timer.elapsed
            self.time_since_1_5_threshold_timer.start()
        else:
            elapsed_time = 0
        return elapsed_time

    def end_of_rain_event_reset(self):
        """
        At the end of a rain event reset all the counters, rates and timers.
        """
        self.rate = 0.0
        self.bucket_tips_counter = 0
        self.tips_time_delta = 0
        self.time_since_1_5_threshold = 0
        self.tips_timer.stop()
        self.tips_timer.reset()
        if self.time_since_1_5_threshold_timer.running:
            self.time_since_1_5_threshold_timer.stop()
            self.time_since_1_5_threshold_timer.reset()
        self.rain_event_scheduler.pause()
        self.rain_event_scheduler.remove_all_jobs()

    @staticmethod
    def rain_rate_calc(bucket_tips, amount_per_tip, tips_time_delta=0.0,
                       time_since_last_tip=0.0, time_since_1_5=0.0):
        """
        Calculate the rainfall rate based on the time interval between bucket
        tips, the time since the last tip and the amount of rainfall required
        to tip the bucket.

        If only one tip has been registered, the hourly rate is simply the
        amount required to make the bucket tip. Otherwise rate calculation is
        based upon the time between the last two tips and the time since the
        last tip was registered.

        :param bucket_tips: The number of bucket tips since the rainfall event
        started.
        :param amount_per_tip: The amount of rainfall required to tip the
        bucket. Normally 0.2 or 0.3 mm.
        :param tips_time_delta: The time between the last two tips in seconds.
        :param time_since_last_tip: The elapsed time since the last
        tip occurred in seconds.
        :param time_since_1_5: The elapsed time since the threshold at which
        the time since the last tip < 1.5 * time between the last two tips
        in minutes.
        :return: The hourly rainfall rate in the same units as used for the
        amount of rainfall required per tip (usually mm/hr)
        """
        tips_time_delta_minutes = tips_time_delta / 60
        time_since_last_tip_mins = time_since_last_tip / 60
        minutes_since_1_5 = time_since_1_5 / 60

        # If this is the first tip, just set the rate to the bucket tip amount.
        if bucket_tips == 1:
            rate = amount_per_tip

        # Tips occurring at approximately the same interval so assume rain
        # falling at about the same rate as calculated using the time delta
        # between the last two tips.
        elif time_since_last_tip_mins < 1.5 * tips_time_delta_minutes:
            rate = (60 / tips_time_delta_minutes) * amount_per_tip

        # Time between tips increasing so assume rainfall rate has slowed.
        elif time_since_last_tip_mins < 2.5 * tips_time_delta_minutes:
            rate = (60 / (tips_time_delta_minutes + minutes_since_1_5)) \
                   * amount_per_tip

        # A long time has elapsed since the last tip so assume the rainfall
        # event has stopped. Set the rate back to zero.
        else:
            rate = 0.0

        if rate < 1:
            rate = round(rate, 1)
        else:
            rate = int(round(rate, 0))

        return rate


class Timer:
    """
    A timer utility class using Python's time.perf_counter and adding functions
    to start, stop, reset and return the elapsed time.
    """

    def __init__(self, func=time.perf_counter):
        self.elapsed = 0.0
        self._func = func
        self._start = None

    def start(self):
        if self._start is not None:
            raise RuntimeError('Timer already started')
        self._start = self._func()

    def stop(self):
        if self._start is None:
            raise RuntimeError('Timer not started')
        end = self._func()
        self.elapsed += end - self._start
        self._start = None

    def reset(self):
        self.elapsed = 0.0

    @property
    def running(self):
        return self._start is not None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()
