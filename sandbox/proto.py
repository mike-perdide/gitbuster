from PyQt4.QtCore import QDate, QTime
from random import random, uniform
from datetime import datetime, timedelta, time

how_many_commits = 12
DEFAULT_AUTHORIZED_HOURS = ((time.min, time.max),)
DEFAULT_AUTHORIZED_WEEKDAYS = (1, 2, 3, 4, 5, 6, 7)

class non_continuous_timelapse:
    def __init__(self, min_date, max_date,
                 authorized_hours=DEFAULT_AUTHORIZED_HOURS,
                 authorized_weekdays=DEFAULT_AUTHORIZED_WEEKDAYS):
        """
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

    def get_total_seconds(self):
        return self.total_seconds

    def datetime_from_seconds(self, seconds):
        """
        """
        keys = self.authorized_ranges.keys()
        keys.sort()
        keys.reverse()

        for stamp in keys:
            if seconds > stamp:
                break

        min_date, max_date = self.authorized_ranges[stamp]

        delta_seconds = seconds - stamp
        return min_date + timedelta(0, delta_seconds)


min_date = datetime(2010, 5, 16)
max_date = datetime(2010, 5, 18)

if min_date == max_date:
    max_date += timedelta(1)
authorized_hours = (
    # Default date : 01/01/2000. We need datetime objets to be able to calculate
    # timedeltas.
    (datetime(2000, 1, 1, 8, 0), datetime(2000, 1, 1, 10, 0)),
    (datetime(2000, 1, 1, 12, 0), datetime(2000, 1, 1, 13, 0)),
)

authorized_weekdays = (0, 1, 2, 3, 4, 5, 6)

truc_truc = non_continuous_timelapse(min_date, max_date,
                                     authorized_hours=authorized_hours,
                                     authorized_weekdays=authorized_weekdays)

#total_seconds = 0
#total_days = 0
# We take all the acceptable timelapses and make a continuous timelapse

#print "=============================================="
#print "  Seconds per day should be    7200:", authorized_seconds_per_day
#print "        Day lapse should be     147:", truc_truc.total_days
#print "    Total seconds should be 1058400:", truc_truc.total_seconds
#print "=============================================="


# Random method
delta = truc_truc.get_total_seconds() / (how_many_commits + 1)
max_error = delta / 2

time_cursor = 0
for commit in xrange(how_many_commits):
    time_cursor += delta
    # The next lines sets the commit_time to time_cursor, plus or less an error
    new_commit_time = time_cursor + int((random() * 2 - 1) * max_error)
    print truc_truc.datetime_from_seconds(new_commit_time)

print "====="

# Uniform method
distribution = [int(random() * truc_truc.get_total_seconds())
                for commit in xrange(how_many_commits)]
distribution.sort()

for commit in xrange(how_many_commits):
    # The next lines sets the commit_time to time_cursor, plus or less an error
    new_commit_time = distribution[commit]
    print truc_truc.datetime_from_seconds(new_commit_time)
