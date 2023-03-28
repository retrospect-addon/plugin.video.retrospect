# coding=utf-8          # NOSONAR
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest

from resources.lib.helpers import jsonhelper
from resources.lib.logger import Logger


class TestJsonHelper(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestJsonHelper, cls).setUpClass()
        Logger.create_logger(None, str(cls), min_log_level=0)

    def test_empty_data(self):
        j = jsonhelper.JsonHelper("", logger=Logger.instance())
        self.assertEqual({}, j.json)

    def test_no_standard_start(self):
        j = jsonhelper.JsonHelper('jQuery18303627530449324564_1370950605750({"success":true});', logger=Logger.instance())
        self.assertEqual({"success": True}, j.json)

    def test_str(self):
        data = '{"success":true}'
        j = jsonhelper.JsonHelper(data, logger=Logger.instance())
        self.assertEqual(data, str(j))

    def test_json_special_chars_quotes(self):
        value = jsonhelper.JsonHelper.convert_special_chars("\\'", do_quotes=False)
        self.assertEqual("\\'", value)
        self.assertNotEqual("'", value)

        value = jsonhelper.JsonHelper.convert_special_chars("\\'", do_quotes=True)
        self.assertEqual("'", value)
        value = jsonhelper.JsonHelper.convert_special_chars('\\"', do_quotes=True)
        self.assertEqual("\"", value)

    def test_get_value(self):
        j = jsonhelper.JsonHelper('{"success":true, "test": 4, "test2": "test", "test3": {"test": true}}', logger=Logger.instance())
        self.assertEqual("test", j.get_value("test2"))
        self.assertEqual(4, j.get_value("test"))
        self.assertEqual(True, j.get_value("success"))
        self.assertEqual(True, j.get_value("test3", "test"))
        self.assertEqual("yes", j.get_value("test3", "test2", fallback="yes"))

    def test_get_value_fallback(self):
        j = jsonhelper.JsonHelper('{"success":true, "test": 4, "test2": "test", "test3": {"test": true}}', logger=Logger.instance())
        self.assertEqual("yes", j.get_value("test3", "test2", fallback="yes"))
        self.assertIsNone(j.get_value("test3", "test2"))

    def test_dumps(self):
        data = {"success": True, "test": 4, "test2": "test", "test3": {"test": True}}
        str_data = jsonhelper.JsonHelper.dump(data, pretty_print=False, sort_keys=True)
        self.assertEqual('{"success": true, "test": 4, "test2": "test", "test3": {"test": true}}', str_data)
        str_data = jsonhelper.JsonHelper.dump(data, pretty_print=True, sort_keys=True)
        self.assertEqual('{\n    "success": true,\n    "test": 4,\n    "test2": "test",\n    "test3": {\n        "test": true\n    }\n}', str_data)

    def test_loads(self):
        data = '{"test": 4, "test3": {"test": true}, "test2": "test", "success": true}'
        str_data = jsonhelper.JsonHelper.loads(data)
        data = {"success": True, "test": 4, "test3": {"test": True}, "test2": "test"}
        self.assertEqual(data, str_data)

    def test_unicode(self):
        data = '{"records":[{"description":"\u849c\u8089","id":282}]}'
        j = jsonhelper.JsonHelper(data, Logger.instance())
        self.assertEqual("蒜肉", j.get_value("records", 0, "description"))
