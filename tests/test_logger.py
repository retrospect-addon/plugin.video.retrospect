# coding=utf-8  # NOSONAR

import tempfile
import unittest
import os
import io

from resources.lib.logger import Logger


class TestLogger(unittest.TestCase):
    def setUp(self):
        self.output_log_file = tempfile.mktemp(prefix="retro_test_", suffix=".log")
        self.__logger = None

        Logger._Logger__logger = None
        print("Using temp path: {0}".format(self.output_log_file))

    def tearDown(self):
        if Logger.exists():
            Logger.instance().close_log()

        if self.__logger and 'handlers' in dir(self.__logger):
            # noinspection PyUnresolvedReferences
            h = self.__logger.handlers.pop(0)
            h.close()
        try:
            if os.path.isfile(self.output_log_file):  # and self._outcome.success:
                os.remove(self.output_log_file)
        except:
            pass

    def test_logger_exists(self):
        self.assertFalse(Logger.exists())
        self.__logger = Logger.create_logger(self.output_log_file, "test_logger_exists")
        self.assertTrue(Logger.exists())

    def test_logger_create(self):
        logger = Logger.create_logger(self.output_log_file, "test_logger_create")
        self.__logger = logger
        self.assertIsNotNone(logger)
        self.assertIsNotNone(Logger.instance())
        self.assertEqual(logger, Logger.instance())

    def test_logger_append(self):
        with io.open(self.output_log_file, "w", encoding='utf-8') as fp:
            fp.write(u"test")
        self.__logger = Logger.create_logger(self.output_log_file, "test_logger_append", append=True)
        self.assertIsNotNone(Logger.instance())

    def test_logger_write_object(self):
        logger = Logger.create_logger(self.output_log_file, "test_logger_write_object",
                                      min_log_level=Logger.LVL_TRACE)
        self.__logger = logger
        logger.trace("Trace")
        logger.debug("Debug")
        logger.info("Info")
        logger.warning("Warning")
        logger.error("Error")
        logger.critical("Critical")
        Logger.instance().close_log()
        with io.open(self.output_log_file, 'r') as fp:
            lines = fp.readlines()
            line_count = len(lines)
            self.assertEqual(7, line_count)
            self.assertTrue(lines[0].rstrip().endswith("Trace"))
            self.assertTrue(lines[1].rstrip().endswith("Debug"))
            self.assertTrue(lines[2].rstrip().endswith("Info"))
            self.assertTrue(lines[3].rstrip().endswith("Warning"))
            self.assertTrue(lines[4].rstrip().endswith("Error"))
            self.assertTrue(lines[5].rstrip().endswith("Critical"))
            self.assertTrue(lines[6].rstrip().endswith("Flushing and closing logfile."))

    def test_logger_write_level(self):
        logger = Logger.create_logger(self.output_log_file, "test_logger_write_level",
                                      min_log_level=Logger.LVL_WARNING)
        self.__logger = logger
        logger.trace("Trace")
        logger.debug("Debug")
        logger.info("Info")
        logger.warning("Warning")
        logger.error("Error")
        logger.critical("Critical")
        Logger.instance().close_log()
        with io.open(self.output_log_file, 'r') as fp:
            lines = fp.readlines()
            line_count = len(lines)
            self.assertEqual(3, line_count)
            self.assertTrue(lines[0].rstrip().endswith("Warning"))
            self.assertTrue(lines[1].rstrip().endswith("Error"))
            self.assertTrue(lines[2].rstrip().endswith("Critical"))

    def test_logger_write_static(self):
        self.__logger = Logger.create_logger(self.output_log_file, "test_logger_write_static",
                                             min_log_level=Logger.LVL_TRACE)
        Logger.trace("Trace")
        Logger.debug("Debug")
        Logger.info("Info")
        Logger.warning("Warning")
        Logger.error("Error")
        Logger.critical("Critical")
        Logger.instance().close_log()
        with io.open(self.output_log_file, 'r') as fp:
            lines = len(fp.readlines())
            self.assertEqual(7, lines)

    def test_logger_write_tuple(self):
        self.__logger = Logger.create_logger(self.output_log_file, "test_logger_write_tuple",
                                             min_log_level=Logger.LVL_TRACE)
        Logger.warning(("test", "nee"))
        Logger.instance().close_log()
        with io.open(self.output_log_file, 'r') as fp:
            lines = len(fp.readlines())
            self.assertEqual(2, lines)

    def test_log_unicode(self):
        self.__logger = Logger.create_logger(self.output_log_file, "UnitTest")
        Logger.info("⠺⠊⠇⠇ ⠹⠻⠑⠋⠕⠗⠑ ⠏⠻⠍⠊⠞ ⠍⠑ ⠞⠕ ⠗⠑⠏⠑⠁⠞⠂ ⠑⠍⠏⠙⠁⠞⠊⠊⠁⠇⠇⠹⠂ ⠹⠁⠞")

        Logger.instance().close_log()
        with io.open(self.output_log_file, 'r', encoding='utf-8') as fp:
            lines = fp.readlines()
            self.assertEqual(2, len(lines))

    def test_traceback(self):
        self.__logger = Logger.create_logger(self.output_log_file, "UnitTest")
        try:
            raise AssertionError("Nope")
        except:
            Logger.error("AssertError", exc_info=True)

        Logger.instance().close_log()
        with io.open(self.output_log_file, 'r') as fp:
            content = fp.readlines()
            lines = len(content)
            self.assertEqual(6, lines)
