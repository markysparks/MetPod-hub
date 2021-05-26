# -*- coding: utf-8 -*-
import time
from unittest import TestCase
from rain_rate_calc import BucketTipHandler
from rain_rate_calc import Timer


class TestRainRateCalc(TestCase):
    """Test the rain rate calculation methods."""

    def setUp(self):
        """Setup the amount of rainfall (in mm) required to to the rain gauge
        bucket, time between two bucket tips, varying times since the last
        bucket tip and the time since the 1.5 threshold"""
        self.amount_per_tip = 0.3
        self.tips_time_delta = 60 * 60
        self.time_since_last_tip_1_5 = 80 * 60
        self.time_since_last_tip_2_5 = 140 * 60
        self.time_since_last_tip_3 = 150 * 60
        self.time_since_1_5 = 2 * 60
        self.bucket_tip_handler = BucketTipHandler(0.3)
        self.rain_rate_calc = BucketTipHandler.rain_rate_calc

    def test_calc_same_rate(self):
        """Test that a single tip produces a rate equivalent to the bucket
        tip amount."""
        rate = self.rain_rate_calc(1, self.amount_per_tip,
                                   self.tips_time_delta,
                                   self.amount_per_tip)
        self.assertEqual(rate, self.amount_per_tip)

    def test_calc_slower_rate_1_5(self):
        """Test that the correct rate is calculated when the time since the
        last tip < 1.5 * gap between the last two tips"""
        rate = self.rain_rate_calc(2, self.amount_per_tip,
                                   self.tips_time_delta,
                                   self.time_since_last_tip_1_5)
        self.assertEqual(rate, self.amount_per_tip)

    def test_calc_slower_rate_2_5(self):
        """Test that the correct rate is calculated when the time since the
                last tip < 2.5 * gap between the last two tips"""
        rate = self.rain_rate_calc(2, self.amount_per_tip,
                                   self.tips_time_delta,
                                   self.time_since_last_tip_2_5,
                                   self.time_since_1_5)
        self.assertAlmostEqual(rate, self.amount_per_tip)

    def test_calc_slower_rate_3(self):
        """Test that the correct rate is calculated when the time since the
                last tip >= 2.5 * gap between the last two tips"""
        rate = self.rain_rate_calc(2, self.amount_per_tip,
                                   self.tips_time_delta,
                                   self.time_since_last_tip_3)
        self.assertEqual(rate, 0.0)

    def test_rate_calc_after_tips(self):
        """Test that the correct rate is calculated a period of time after
        a bucket tip. As time continues after the last bucket tip, the rate
        should be updated to reflect a decrease. Should another tip
        occur, then the rate should be recalculated base on the time gap
        between the two last tips. If no tips have occurred for a significant
        time then the rain event is deemed to have ended and the rate reset
        to zero."""
        self.bucket_tip_handler.bucket_tips_counter = 0
        self.bucket_tip_handler.process_bucket_tip()  # Tip no. 1
        self.assertEqual(self.bucket_tip_handler.bucket_tips_counter, 1)
        self.assertEqual(self.bucket_tip_handler.rate,
                         self.bucket_tip_handler.amount_per_tip)
        time.sleep(30)  # 30 sec gap between tips 1 and 2.
        self.bucket_tip_handler.process_bucket_tip()  # Tip no. 2
        self.assertEqual(self.bucket_tip_handler.bucket_tips_counter, 2)
        # Rate base on two tips and a time between them of 30 secs.
        self.assertEqual(self.bucket_tip_handler.rate, 36)

        # Rate if time since last tip < 1.5 * gap between last two tips.
        time.sleep(15)
        self.assertEqual(self.bucket_tip_handler.rate, 36)

        # Rate if time since last tip < 2.5 * gap between last two tips
        time.sleep(50)
        self.assertEqual(self.bucket_tip_handler.rate, 24)

        # Check another tip action
        self.bucket_tip_handler.process_bucket_tip()
        self.assertEqual(self.bucket_tip_handler.rate, 17)

        # Rate if time since last tip > 2.5 * gap between last two tips
        # End of rain event, reset rate.
        time.sleep(180)
        self.assertEqual(self.bucket_tip_handler.rate, 0.0)
        self.assertEqual(self.bucket_tip_handler.bucket_tips_counter, 0)


class TestBucketTipAction(TestCase):
    """Test the methods for the correct handling of bucket tips"""
    def setUp(self):
        self.bucket_tip_handler = BucketTipHandler(0.3)

    def test_single_tip(self):
        """Test that a single tip produces the correct rate"""
        self.bucket_tip_handler.bucket_tips_counter = 0
        self.bucket_tip_handler.process_bucket_tip()
        self.assertEqual(self.bucket_tip_handler.rate,
                         self.bucket_tip_handler.amount_per_tip)

    def test_multiple_tips(self):
        """Test that the correct rate is calculated for multiple tips with
        varying time intervals"""
        self.bucket_tip_handler.bucket_tips_counter = 0
        self.bucket_tip_handler.process_bucket_tip()
        self.assertEqual(self.bucket_tip_handler.bucket_tips_counter, 1)
        self.assertEqual(self.bucket_tip_handler.rate,
                         self.bucket_tip_handler.amount_per_tip)
        time.sleep(5)
        self.bucket_tip_handler.process_bucket_tip()
        self.assertEqual(self.bucket_tip_handler.bucket_tips_counter, 2)
        self.assertAlmostEqual(self.bucket_tip_handler.rate, 216, -1)
        time.sleep(10)
        self.bucket_tip_handler.process_bucket_tip()
        self.assertEqual(self.bucket_tip_handler.bucket_tips_counter, 3)
        self.assertAlmostEqual(self.bucket_tip_handler.rate, 108, -1)
        time.sleep(5)
        self.bucket_tip_handler.process_bucket_tip()
        self.assertEqual(self.bucket_tip_handler.bucket_tips_counter, 4)
        self.assertAlmostEqual(self.bucket_tip_handler.rate, 215, -1)
        time.sleep(5)
        self.bucket_tip_handler.process_bucket_tip()
        self.assertEqual(self.bucket_tip_handler.bucket_tips_counter, 5)
        self.assertAlmostEqual(self.bucket_tip_handler.rate, 215, -1)


class TestTimer(TestCase):
    """Test the functions of the rain tip stopwatch timer"""

    def setUp(self):
        self.timer = Timer()

    def test_timer_stop_start_reset_functions(self):
        """Test that the timer starts, stops and resets correctly."""
        self.timer.start()
        self.assertTrue(self.timer.running)
        self.timer.stop()
        self.assertFalse(self.timer.running)
        self.timer.reset()
        self.assertEqual(self.timer.elapsed, 0.0)

    def test_timer_elapsed_time_function(self):
        """Test that the timer returns the correct elapsed time."""
        self.timer.start()
        time.sleep(3)
        self.timer.stop()
        self.assertAlmostEqual(self.timer.elapsed, 3, 0)
        self.timer.reset()

    def test_timer_runtime_warnings(self):
        """Test that the timer raises the correct runtime errors if its
        started when already running or stopped when already stopped."""
        self.timer.start()
        with self.assertRaisesRegex(RuntimeError, 'Timer already started'):
            self.timer.start()
        self.timer.stop()
        with self.assertRaisesRegex(RuntimeError, 'Timer not started'):
            self.timer.stop()
