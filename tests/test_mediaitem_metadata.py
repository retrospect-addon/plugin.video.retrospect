# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
from unittest.mock import Mock, patch

from resources.lib import mediatype
from resources.lib.logger import Logger


class TestMediaItemMetadata(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Logger.create_logger(None, cls.__name__)
        from resources.lib.mediaitem import MediaItem
        cls.media_item_type = MediaItem

    def setUp(self):
        # Restrict the doubles to the Nexus API: legacy setInfo is not available.
        self.video = Mock(spec=[
            "setTitle", "setMediaType", "setYear", "setDuration", "setGenres",
            "setPlot", "setTvShowTitle", "setSeason", "setEpisode",
            "setFirstAired", "setTrackNumber",
        ])
        self.music = Mock(spec=[
            "setTitle", "setMediaType", "setYear", "setDuration", "setGenres",
            "setTrack", "setArtist", "setAlbumArtist",
        ])
        self.kodi_item = Mock(spec=[
            "getVideoInfoTag", "getMusicInfoTag", "setDateTime", "setLabel",
            "setLabel2", "setProperty", "setArt", "setContentLookup",
        ])
        self.kodi_item.getVideoInfoTag.return_value = self.video
        self.kodi_item.getMusicInfoTag.return_value = self.music
        factory = patch("resources.lib.mediaitem.kodifactory.list_item",
                        return_value=self.kodi_item)
        factory.start()
        self.addCleanup(factory.stop)

    def test_episode_metadata_and_iso_date(self):
        item = self.media_item_type("Episode &amp; title", "https://example.com", mediatype.EPISODE)
        item.description = "Plot &amp; details"
        item.set_season_info(2, 3, "Series")
        item.set_date(2026, 9, 20)
        item.set_info_label("duration", 123.75)
        item.set_info_label("genre", "Drama / Comedy")

        self.assertIs(item.get_kodi_item(), self.kodi_item)

        self.video.setTitle.assert_called_once_with("Episode & title ")
        self.video.setPlot.assert_called_once_with("Plot & details")
        self.video.setMediaType.assert_called_once_with("episode")
        self.video.setSeason.assert_called_once_with(2)
        self.video.setEpisode.assert_called_once_with(3)
        self.video.setTvShowTitle.assert_called_once_with("Series")
        self.video.setDuration.assert_called_once_with(123)
        self.video.setGenres.assert_called_once_with(["Drama", "Comedy"])
        self.video.setFirstAired.assert_called_once_with("2026-09-20")
        self.video.setYear.assert_called_once_with(2026)
        self.kodi_item.setDateTime.assert_called_once_with("2026-09-20")
        self.kodi_item.setProperty.assert_called_once_with("IsPlayable", "true")
        self.kodi_item.getMusicInfoTag.assert_not_called()
        self.assertEqual(123.75, item.get_info_label("duration"))

    def test_music_artist_lists_and_track(self):
        item = self.media_item_type("Classical", "https://example.com", mediatype.SONG)
        item.set_info_label("tracknumber", "4")
        item.set_info_label("artist", ["Performer A", "Performer B"])
        item.set_info_label("albumartist", ["Composer A", "Composer B"])
        item.set_info_label("duration", 42.9)
        item.set_info_label("genre", ["Classical", "Piano"])
        item.set_date(2025, 3, 2)
        item.get_kodi_item()

        self.music.setTrack.assert_called_once_with(4)
        self.music.setArtist.assert_called_once_with("Performer A / Performer B")
        self.music.setAlbumArtist.assert_called_once_with("Composer A / Composer B")
        self.music.setDuration.assert_called_once_with(42)
        self.music.setGenres.assert_called_once_with(["Classical", "Piano"])
        self.music.setYear.assert_called_once_with(2025)
        self.kodi_item.getVideoInfoTag.assert_not_called()

    def test_optional_genre_and_missing_date(self):
        item = self.media_item_type("Video", "https://example.com", mediatype.VIDEO)
        item.set_info_label("genre", None)
        item.set_info_label("duration", 0)
        item.get_kodi_item()

        self.video.setGenres.assert_not_called()
        self.video.setDuration.assert_called_once_with(0)
        self.video.setFirstAired.assert_not_called()
        self.video.setYear.assert_not_called()
        self.kodi_item.setDateTime.assert_not_called()

    def test_folder_metadata_without_playable_or_media_type(self):
        for media_type in (mediatype.FOLDER, mediatype.PAGE):
            with self.subTest(media_type=media_type):
                self.video.reset_mock()
                self.kodi_item.reset_mock()
                item = self.media_item_type("Folder", "https://example.com", media_type)
                item.description = "Folder description"
                item.get_kodi_item()

                self.video.setPlot.assert_called_once_with("Folder description")
                self.video.setMediaType.assert_not_called()
                self.kodi_item.setProperty.assert_not_called()
