# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from resources.lib.version import Version


class TestVersion(unittest.TestCase):

    def setUp(self):
        self.version2021 = Version(version="2.0.2.1")
        self.version2121 = Version(version="2.1.2.1")
        self.version2121 = Version(version="2.1.2.11")
        self.version2130 = Version(version="2.1.3.0")
        self.version213 = Version(version="2.1.3")
        self.version2135 = Version(version="2.1.3.5")
        self.version2130a1 = Version(version="2.1.3.0~alpha1")
        self.version213b1 = Version(version="2.1.3~beta1")
        self.version2130b1 = Version(version="2.1.3.0~beta1")
        self.version2130b2 = Version(version="2.1.3.0~beta2")
        self.version2130b11 = Version(version="2.1.3.0~beta11")
        self.version2130b = Version(version="2.1.3.0~beta")
        self.version2130a = Version(version="2.1.3.0~alpha")
        return

    def test_text_init(self):
        v_value = "2.1.3.1"
        str_value = "2.1.3.1"
        v = Version(version=v_value)
        self.assertEqual(2, v.major)
        self.assertEqual(1, v.minor)
        self.assertEqual(3, v.revision)
        self.assertEqual(1, v.build)
        self.assertIsNone(v.buildType)
        self.assertEqual(str_value, str(v))

    def test_text_init_named(self):
        v_value = "2.1.3.0~alpha1"
        v = Version(version=v_value)
        self.assertEqual(2, v.major)
        self.assertEqual(1, v.minor)
        self.assertEqual(3, v.revision)
        self.assertEqual(0, v.build)
        self.assertEqual("alpha1", v.buildType)

    def test_to_string(self):
        for v_value in ("2.1.3.0~alpha1", "2.1.3.0"):
            v = Version(version=v_value)
            self.assertEqual(v_value, str(v))

    def test_keyword_parameter_init(self):
        v = Version(major=2, minor=1, build=3, revision=4)
        self.assertEqual(2, v.major)
        self.assertEqual(1, v.minor)
        self.assertEqual(3, v.revision)
        self.assertEqual(4, v.build)
        self.assertIsNone(v.buildType)

    def test_are_compatible(self):
        v0 = Version(version="2.1.3")
        v1 = Version(version="2.1.3.1")
        v2 = Version(version="2.1.3.2")
        v3 = Version(version="2.0.1.2")
        a4 = Version(version="2.0.1.2~alpha1")
        b5 = Version(version="2.0.1~beta1")
        self.assertTrue(v1.are_compatible(v0))
        self.assertTrue(v1.are_compatible(v2))
        self.assertFalse(v1.are_compatible(v3))
        self.assertTrue(v3.are_compatible(a4))
        self.assertTrue(v3.are_compatible(b5))
        self.assertFalse(v3.are_compatible(None))

    def test_lt(self):
        self.assertLess(self.version2021, self.version2130)
        self.assertLess(self.version2130, self.version2135)
        self.assertLessEqual(self.version2021, self.version2130)
        self.assertLessEqual(self.version2130, self.version2135)
        self.assertLess(self.version2130a1, self.version213b1)
        self.assertLess(self.version213b1, self.version2130b2)
        self.assertLess(self.version213b1, self.version2130)
        self.assertLess(self.version2021, self.version213b1)
        self.assertLess(self.version2121, self.version2130)
        self.assertLess(self.version2130a, self.version2130b)
        self.assertLess(self.version2130b, self.version2130b1)
        self.assertLess(self.version2130b2, self.version2130b11)
        self.assertLess(Version(major=1), Version(major=2))
        self.assertFalse(Version(major=1) < Version(major=1, build_type="alpha1"))
        self.assertLess(Version("2.1.1.0012~beta1"), Version("2.1.1.0012~beta10"))
        self.assertLess(Version("2.1.1.0~beta1"), Version("2.1.1.0"))
        self.assertLess(Version("2.1.1~beta1"), Version("2.1.1"))
        self.assertLess(Version("2.1.1.0~beta1"), Version("2.1.1"))
        self.assertLess(Version("2.1.1.2"), Version("2.1.1.12"))

    def test_eq(self):
        self.assertEqual(self.version2130, self.version213)
        self.assertEqual(self.version2130, Version(version="2.1.3.0"))
        self.assertEqual(self.version213b1, self.version2130b1)
        self.assertEqual(self.version2130b11, self.version2130b11)
        self.assertEqual(Version("2.1.1.0012~beta1"), Version("2.1.1.0012~beta1"))
        self.assertEqual(Version("2.1.1~beta1"), Version("2.1.1.0000~beta1"))

    def test_noteq(self):
        self.assertNotEqual(self.version2130, self.version2021)
        self.assertNotEqual(self.version2130, None)
        self.assertNotEqual(Version("2.1.1.0012~beta1"), Version("2.1.1.0012~beta2"))
        self.assertNotEqual(Version("2.1.1.0012~beta1"), Version("2.1.1.0013~beta1"))

    def test_gt(self):
        self.assertGreater(Version("2.1.1.0013"), Version("2.1.1~beta13"))
        self.assertGreater(Version("2.1.1.0013"), Version("2.1.1~beta14"))
        self.assertGreater(Version("2.1.1.0013"), Version("2.1.1.0012"))
        self.assertGreater(Version("2.1.1.0012~beta2"), Version("2.1.1.0012~beta1"))
        self.assertGreater(self.version2130, self.version2021)
        self.assertGreater(self.version2135, self.version2130)
        self.assertGreaterEqual(self.version2130, self.version2021)
        self.assertGreaterEqual(self.version2135, self.version2130)
        self.assertGreater(self.version213b1, self.version2130a1)
        self.assertGreater(self.version2130b2, self.version213b1)
        self.assertGreater(self.version2130, self.version213b1)
        self.assertGreater(self.version213b1, self.version2021)
        self.assertGreater(self.version2130b11, self.version2130b2)

    def test_less_none(self):
        self.assertFalse(Version("2.1.1.2") < None)
        self.assertFalse(Version("2.1.1.2") <= None)

    def test_gt_none(self):
        self.assertGreater(self.version2130b11, None)
        self.assertGreaterEqual(self.version2130b11, None)

    def test_build_number_same(self):
        version1 = Version(version="2.1.3.1")
        version2 = Version(version="2.1.3.0001")
        self.assertEqual(version1, version2)

    def test_build_number_differ(self):
        version1 = Version(version="2.1.3.0001")
        version2 = Version(version="2.1.3.0002")
        self.assertLess(version1, version2)

    def test_build_number_differ_beta(self):
        version1 = Version(version="2.1.3~beta1")
        version2 = Version(version="2.1.3.0000")
        self.assertLess(version1, version2)

    def test_str(self):
        self.assertEqual("2.1.3.0", str(self.version2130))
        self.assertEqual("2.1.3.0", repr(self.version2130))
        self.assertEqual("None", str(Version(version="")))
        self.assertEqual("1", str(Version(major=1)))
        self.assertEqual("1.1", str(Version(major=1, minor=1)))
        self.assertEqual("1.1.1", str(Version(major=1, minor=1, build=1)))
        self.assertEqual("1~alpha1", str(Version(major=1, build_type="alpha1")))
        self.assertEqual("1.1~alpha1", str(Version(major=1, minor=1, build_type="alpha1")))
        self.assertEqual("1.1.1~alpha1", str(Version(major=1, minor=1, build=1, build_type="alpha1")))

    def test_init_errors(self):
        with self.assertRaises(ValueError):
            Version()
        with self.assertRaises(ValueError):
            Version(version="1.1", major=1)
        with self.assertRaises(ValueError):
            Version(build=1)
        with self.assertRaises(ValueError):
            Version(major=1, build=1)
        with self.assertRaises(ValueError):
            Version(major=1, minor=1, revision=1)

    def test_compare_none(self):
        self.assertIsNotNone(Version("1.0"))
