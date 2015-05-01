#===============================================================================
# LICENSE Retrospect-Framework - CC BY-NC-ND
#===============================================================================
# This work is licenced under the Creative Commons
# Attribution-Non-Commercial-No Derivative Works 3.0 Unported License. To view a
# copy of this licence, visit http://creativecommons.org/licenses/by-nc-nd/3.0/
# or send a letter to Creative Commons, 171 Second Street, Suite 300,
# San Francisco, California 94105, USA.
#===============================================================================

from addonsettings import AddonSettings


class LanguageHelper:
    UnknownId = 1
    AllFavouritesId = 30500
    FavouriteId = 30501
    FavouritesId = 30502
    ChannelFavourites = 30503
    AddToId = 30504
    HideId = 30505
    RemoveId = 30506
    ChannelsId = 30507
    NoFavsId = 30508
    NoPlaybackId = 30509
    NoUpdatesId = 30511
    RestartId = 30512
    UpdateCompleteId = 30513
    UpdateFailedId = 30514
    UpdateFailed2Id = 30515
    NewVersionId = 30516
    NewVersion2Id = 30517
    NewFrameworkId = 30518
    NoUpdatedChannelsId = 30519
    RepoWarningId = 30520
    RepoWarningDetailId = 30521
    ChannelMessageId = 30522
    ErrorId = 30523
    NoVideosId = 30524
    NoStreamsId = 30525
    ProxyOkId = 30526
    ProxyNokId = 30527
    AddOnSettingsId = 30528
    RefreshListId = 30529
    CheckUpdatesId = 30530

    InitializingId = 30531
    ImportCommonId = 30532
    DeterminSkinId = 30533
    CheckForUpdatesId = 30534
    RepoVerificationId = 30535
    CacheCheckId = 30536
    CacheCleanupId = 30537

    NoLiveStreamId = 30538
    NoLiveStreamTitleId = 30539
    GeoLockedId = 30540
    QueueItemId = 30541
    StartingAddonId = 30542
    SeasonId = 30543
    EpisodeId = 30544
    StartWith = 30545
    OtherChars = 30546
    MorePages = 30547
    Clips = 30548
    ErrorList = 30549
    ErrorNoEpisodes = 30550

    Active = 30068
    ShowChannelSettings = 30069

    __Categories = {"None": 30100,
                    "Regional": 30101,
                    "National": 30102,
                    "Video": 30103,
                    "Radio": 30104,
                    "Sport": 30105,
                    "Kids": 30106,
                    "Tech": 30107,
                    "Other": 30108}

    def __init__(self):
        pass

    @staticmethod
    def GetLocalizedCategory(categoryName):
        """

        """
        stringId = LanguageHelper.__Categories.get(categoryName, None)
        if not stringId:
            return categoryName

        return LanguageHelper.GetLocalizedString(stringId, False)

    @staticmethod
    def GetLocalizedString(stringId, splitOnPipes=True, replacePipes=False):
        """ Returns a localized Add-on string using the defined StringId's.

        Arguments:
        stringId - int - The ID for the string

        Keyword arguments:
        splitOnPipes - Boolean - If true, | cause a split and a list will be returned.
        replacePipes - Boolean - If true, | will be replaced by \n.

        """

        value = AddonSettings.GetLocalizedString(stringId)
        # value = xbmc.getLocalizedString(stringId)
        # print "%s - %s" % (stringId, value)
        if splitOnPipes and "|" in value:
            return value.split("|")
        elif replacePipes and "|" in value:
            return value.replace("|", "\n")
        else:
            return value
