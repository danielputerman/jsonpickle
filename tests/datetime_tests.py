# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Jason R. Coombs <jaraco@jaraco.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import unittest
import datetime
import time

import jsonpickle

from jsonpickle._samples import ObjWithDate


# UTC implementation from Python 2.7 docs
class UTC(datetime.tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return datetime.timedelta()

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return datetime.timedelta()

utc = UTC()


class TimestampedVariable(object):
    def __init__(self, value=None):
        self._value = value
        self._dt_read = datetime.datetime.utcnow()
        self._dt_write = self._dt_read

    def get(self, default_value=None):
        if self._dt_read == None and self._dt_write == None:
            value = default_value
            self._value = value
            self._dt_write = datetime.datetime.utcnow()
        else:
            value = self._value
        self._dt_read = datetime.datetime.utcnow()
        return value

    def set(self, new_value):
        self._dt_write = datetime.datetime.utcnow()
        self._value = new_value

    def __repr__(self):
        dt_now = datetime.datetime.utcnow()
        td_read = dt_now - self._dt_read
        td_write = dt_now - self._dt_write
        s = '<TimestampedVariable>\n'
        s += '  value: ' + str(self._value) + '\n'
        s += '  dt_read : ' + str(self._dt_read) + ' (%s ago)' % td_read + '\n'
        s += '  dt_write: ' + str(self._dt_write) + ' (%s ago)' % td_write + '\n'
        return s

    def erasable(self, td=datetime.timedelta(seconds=1)):
        dt_now = datetime.datetime.utcnow()
        td_read = dt_now - self._dt_read
        td_write = dt_now - self._dt_write
        return( ( td_read > td ) and ( td_write > td ) )


class PersistantVariables(object):

    def __init__(self):
        self._data = {}

    def __getitem__(self, key):
        if key not in self._data:
            self._data[key] = TimestampedVariable(None)

        return self._data[key]

    def __setitem__(self, key, value):
        if key not in self._data:
            self._data[key] = TimestampedVariable(value)

        return self._data[key]

    def __repr__(self):
        return str(self._data)


class DateTimeInnerReferenceTestCase(unittest.TestCase):

    def test_object_with_inner_datetime_refs(self):
        pvars = PersistantVariables()
        pvars['z'] = 1
        pvars['z2'] = 2
        pickled = jsonpickle.encode(pvars)
        obj = jsonpickle.decode(pickled)

        # ensure the references are valid
        self.assertTrue(obj['z']._dt_read is obj['z']._dt_write)
        self.assertTrue(obj['z2']._dt_read is obj['z2']._dt_write)

        # ensure the values are valid
        self.assertEqual(obj['z'].get(), 1)
        self.assertEqual(obj['z2'].get(), 2)

        # ensure get() updates _dt_read
        self.assertTrue(obj['z']._dt_read is not obj['z']._dt_write)
        self.assertTrue(obj['z2']._dt_read is not obj['z2']._dt_write)


class DateTimeTests(unittest.TestCase):

    def _roundtrip(self, obj):
        """
        pickle and then unpickle object, then assert the new object is the
        same as the original.
        """
        pickled = jsonpickle.encode(obj)
        unpickled = jsonpickle.decode(pickled)
        self.assertEquals(obj, unpickled)

    def test_datetime(self):
        """
        jsonpickle should pickle a datetime object
        """
        self._roundtrip(datetime.datetime.now())

    def test_date(self):
        """
        jsonpickle should pickle a date object
        """
        self._roundtrip(datetime.datetime.today())

    def test_time(self):
        """
        jsonpickle should pickle a time object
        """
        self._roundtrip(datetime.datetime.now().time())

    def test_timedelta(self):
        """
        jsonpickle should pickle a timedelta object
        """
        self._roundtrip(datetime.timedelta(days=3))

    def test_utc(self):
        """
        jsonpickle should be able to encode and decode a datetime with a
        simple, pickleable UTC tzinfo.
        """
        self._roundtrip(datetime.datetime.utcnow().replace(tzinfo=utc))

    def test_unpickleable(self):
        """
        If 'unpickleable' is set on the Pickler, the date objects should be
        simple, human-readable strings.
        """
        obj = datetime.datetime.now()
        pickler = jsonpickle.pickler.Pickler(unpicklable=False)
        flattened = pickler.flatten(obj)
        self.assertEqual(str(obj), flattened)

    def test_object_with_datetime(self):
        test_obj = ObjWithDate()
        json = jsonpickle.encode(test_obj)
        test_obj_decoded = jsonpickle.decode(json)
        self.assertEqual(test_obj_decoded.data['ts'],
                         test_obj_decoded.data_ref['ts'])

    def test_struct_time(self):
        expect = time.struct_time([1,2,3,4,5,6,7,8,9])
        json = jsonpickle.encode(expect)
        actual = jsonpickle.decode(json)
        self.assertEqual(type(actual), time.struct_time)
        self.assertEqual(expect, actual)



def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DateTimeTests))
    suite.addTest(unittest.makeSuite(DateTimeInnerReferenceTestCase))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
