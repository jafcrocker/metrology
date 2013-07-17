from unittest import TestCase
from mock import patch
from decorator import decorator
from metrology.stats.sample import UniformSample, ExponentiallyDecayingSample
import random


class UniformSampleTest(TestCase):
    def test_sample(self):
        sample = UniformSample(100)
        for i in range(1000):
            sample.update(i)
        snapshot = sample.snapshot()
        self.assertEqual(sample.size(), 100)
        self.assertEqual(snapshot.size(), 100)

        for value in snapshot.values:
            self.assertTrue(value < 1000.0)
            self.assertTrue(value >= 0.0)


class ExponentiallyDecayingSampleTest(TestCase):
    def test_sample_1000(self):
        sample = ExponentiallyDecayingSample(100, 0.99)
        for i in range(1000):
            sample.update(i)
        self.assertEqual(sample.size(), 100)
        snapshot = sample.snapshot()
        self.assertEqual(snapshot.size(), 100)

        for value in snapshot.values:
            self.assertTrue(value < 1000.0)
            self.assertTrue(value >= 0.0)

    def test_sample_10(self):
        sample = ExponentiallyDecayingSample(100, 0.99)
        for i in range(10):
            sample.update(i)
        self.assertEqual(sample.size(), 10)

        snapshot = sample.snapshot()
        self.assertEqual(snapshot.size(), 10)

        for value in snapshot.values:
            self.assertTrue(value < 10.0)
            self.assertTrue(value >= 0.0)

    def test_sample_100(self):
        sample = ExponentiallyDecayingSample(1000, 0.01)
        for i in range(100):
            sample.update(i)
        self.assertEqual(sample.size(), 100)

        snapshot = sample.snapshot()
        self.assertEqual(snapshot.size(), 100)

        for value in snapshot.values:
            self.assertTrue(value < 100.0)
            self.assertTrue(value >= 0.0)

    def timestamp_to_priority_is_noop(f):
        """
        Decorator that patches ExponentiallyDecayingSample class such that the
        timestamp->priority function is a no-op.
        """
        weight_fn =  "metrology.stats.sample.ExponentiallyDecayingSample.weight"
        return patch(weight_fn, lambda self, x : x)(
               patch("random.random", lambda:1.0 )
                   (f))


    @timestamp_to_priority_is_noop
    def test_sample_eviction(self):
        kSampleSize= 10
        kDefaultValue = 1.0
        sample = ExponentiallyDecayingSample(kSampleSize, 0.01)

        timeStamps = range(1, kSampleSize*2)
        for count, timeStamp in enumerate(timeStamps):
            sample.update(kDefaultValue, timeStamp)
            self.assertLessEqual(len(sample.values), kSampleSize)
            self.assertLessEqual(len(sample.values), count+1)
            expected_min_key = timeStamps[max(0,count+1-kSampleSize)]
            self.assertEqual(min(sample.values)[0], expected_min_key)


    @timestamp_to_priority_is_noop
    def test_sample_ordering(self):
        kSampleSize= 3
        sample = ExponentiallyDecayingSample(kSampleSize, 0.01)

        timestamps =  range(1, kSampleSize+1)
        values = ["VAL_"+str(i) for i in timestamps]
        expected = zip(timestamps, values)
        for timestamp, value in expected:
            sample.update(value, timestamp)
        self.assertEqual(sorted(sample.values), expected)

        # timestamp less than any existing => no-op
        sample.update(None, 0.5 )
        self.assertEqual(sorted(sample.values), expected)

        # out of order insertions
        expected = [3.0, 4.0, 5.0]
        sample.update(None, 5.0)
        sample.update(None, 4.0)
        self.assertEqual(sorted(k for k,_  in sample.values), expected)

        # collision
        marker = "MARKER"
        replacement_timestamp = 5.0
        expected = [4.0, 5.0, 5.0]
        sample.update(marker, replacement_timestamp)
        self.assertEqual(sorted(k for k,_  in sample.values), expected)

        replacement_timestamp = 4.0
        expected = [4.0, 5.0, 5.0]
        sample.update(marker, replacement_timestamp)
        self.assertEqual(sorted(k for k,_  in sample.values), expected)



