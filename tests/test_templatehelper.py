# SPDX-License-Identifier: CC-BY-NC-SA-4.0

import unittest
import io
import os

from resources.lib.helpers.templatehelper import TemplateHelper
from resources.lib.logger import Logger


class TestTemplateHelper(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Logger.create_logger(None, str(cls), min_log_level=0)

    def setUp(self):
        self.__currentPath = os.path.dirname(__file__)
        self.__pathFull = os.path.abspath(os.path.join(self.__currentPath, "data", "test_templatehelper_001_input.xml"))
        self.__pathSimple = os.path.abspath(os.path.join(self.__currentPath, "data", "test_templatehelper_002_input.xml"))
        self.__template = None
        with io.open(self.__pathSimple) as fp:
            self.__template = fp.read()
        self.__logger = Logger.instance()

    def test_TemplateHelper_Error(self):
        th = TemplateHelper(self.__logger, template_path=self.__pathFull)
        with self.assertRaises(ValueError):
            th.get_index_of("general", "channel_89673FF0-5EF3-11E0-8CC9-494DDFD72085_visible")

    def test_TemplateHelper_InvalidCategoryError(self):
        th = TemplateHelper(self.__logger, template_path=self.__pathFull)
        with self.assertRaises(KeyError):
            th.get_index_of("general2", "channel_89673FF0-5EF3-11E0-8CC9-494DDFD72085_visible")

    def test_TemplateHelper_Offset(self):
        th = TemplateHelper(self.__logger, template=self.__template)
        selected_country_index = th.get_index_of("second", "selected_country")
        self.assertEqual(0, selected_country_index)
        german_proxy_index = th.get_index_of("second", "other_proxy_type")
        self.assertEqual(2, german_proxy_index)
        offet = th.get_offset("second", "selected_country", "other_proxy_type")
        self.assertEqual(-2, offet)

    def test_TemplateHelper_Transform(self):
        th = TemplateHelper(self.__logger, template=self.__template)
        result = th.transform()
        with io.open(os.path.join(self.__currentPath, "data", "test_templatehelper_002_output.xml"), "r", encoding='utf-8') as fp:
            expected = fp.read()
        self.assertEqual(expected, result)

    # @unittest.skip("Not yet working")
    def test_TemplateHelper_TransformFull(self):
        th = TemplateHelper(self.__logger, template_path=self.__pathFull)
        result = th.transform()
        with io.open(os.path.join(self.__currentPath, "data", "test_templatehelper_001_output.xml"), "r", encoding="utf-8") as fp:
            expected = fp.read()
        self.assertEqual(expected, result)
