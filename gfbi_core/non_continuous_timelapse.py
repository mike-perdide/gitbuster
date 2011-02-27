# non_continuous_timelapse.py
# Copyright (C) 2011 Julien Miotte <miotte.julien@gmail.com>
#
# This module is part of gfbi_core and is released under the GPLv3
# License: http://www.gnu.org/licenses/gpl-3.0.txt
#
# -*- coding: utf-8 -*-
from datetime import time

DEFAULT_AUTHORIZED_HOURS = ((time.min, time.max),)
DEFAULT_AUTHORIZED_WEEKDAYS = (0, 1, 2, 3, 4, 5, 6)

class non_continuous_timelapse:
    def __init__(self, authorized_dates,
                 authorized_hours=DEFAULT_AUTHORIZED_HOURS,
                 authorized_weekdays=DEFAULT_AUTHORIZED_WEEKDAYS):
        """
            Simulates a continuous timelapse out of hours, dates and weekdays
            limits.

            :param min_date:
                datetime object describing the min authorized date
            :param max_date:
                datetime object describing the max authorized date
            :param authorized_hours:
                tuple containing 2-tuples of the limits of the authorized time
                ranges
            :param authorized_weekdays:
                tuple containing the authorized weekdays, described by their
                number in a week starting by monday -> 1.
        """
        self.authorized_ranges = {}
        self.total_days = 0
        self.total_seconds = 0

        min_date, max_date = authorized_dates
        days_lapse = (max_date - min_date).days

        cur_date = min_date

        while cur_date != max_date:
            if cur_date.weekday() in authorized_weekdays:
                self.total_days += 1
                for time_min, time_max in authorized_hours:
                    down_limit = datetime(
                        cur_date.year, cur_date.month, cur_date.day,
                        time_min.hour, time_min.minute, time_min.second,
                        time_min.microsecond)
                    up_limit = datetime(
                        cur_date.year, cur_date.month, cur_date.day,
                        time_max.hour, time_max.minute, time_max.second,
                        time_max.microsecond)

                    delta = (up_limit - down_limit)
                    self.authorized_ranges[self.total_seconds] = (down_limit,
                                                                  up_limit)

                    self.total_seconds += delta.seconds

            cur_date += timedelta(1)

        if not self.authorized_ranges:
            raise Exception("The non-continuous timelapse is empty.")

    def get_total_seconds(self):
        """
            Returns the number of seconds of the simulated timelapse.
        """
        return self.total_seconds

    def datetime_from_seconds(self, seconds):
        """
            Returns an absolute datetime out of a relative number of seconds
            since the beggining of the simulated timelapse.

            :param seconds:
                The relative number of seconds since the beggining of the
                simulated timelapse.
        """
        keys = self.authorized_ranges.keys()
        keys.sort()
        keys.reverse()

        stamp = 0
        for stamp in keys:
            if seconds > stamp:
                break

        min_date, max_date = self.authorized_ranges[stamp]

        delta_seconds = seconds - stamp
        return min_date + timedelta(0, delta_seconds)


