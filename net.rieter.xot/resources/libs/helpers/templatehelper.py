import re
from StringIO import StringIO
# from xml.dom import minidom
from xml.etree import ElementTree


class TemplateHelper:
    def __init__(self, logger, templatePath=None, template=None):
        self.__logger = logger
        self.__settingsIndex = {}
        self.__relativeRegex = re.compile("(%([^%]+)%)")

        self.__templateLines = []
        if templatePath:
            with file(templatePath) as fp:
                self.__templateLines = fp.readlines()
        else:
            fp = StringIO(template)
            self.__templateLines = fp.readlines()

        # self.__templatePath = templatePath
        # self.__templateData = template

        if templatePath:
            self.__template = ElementTree.parse(templatePath)
        else:
            self.__template = ElementTree.fromstring(template)

        categories = self.__template.findall('.//category')
        for category in categories:
            categorySettingsIndex = []
            categoryId = category.attrib["id"]
            self.__settingsIndex[categoryId] = categorySettingsIndex

            settings = category.findall('.//setting')
            self.__logger.Debug("Found %d settings in Category '%s'", len(settings), categoryId)
            for node in settings:
                # setting = node.attributes.get("id", None)
                settingId = node.attrib.get("id", ElementTree.tostring(node).strip())
                nodeStr = ElementTree.tostring(node).strip()
                categorySettingsIndex.append(settingId)
                self.__logger.Trace("%02d: %s - %s", len(categorySettingsIndex), settingId, nodeStr)

    def GetOffset(self, categoryId, referenceId, settingId, skip=0):
        if self.__settingsIndex[categoryId].count(referenceId) > 1:
            raise ValueError("Multiple reference setting indexes found for %s." % (referenceId,))

        if self.__settingsIndex[categoryId].count(settingId) > 1:
            # raise ValueError("Multiple setting indexes found for %s. Don't know which one to use." % (settingId,))
            self.__logger.Warning("Multiple values found for %s, using #%s", settingId, skip)

        return self.GetIndexOf(categoryId, referenceId) - self.GetIndexOf(categoryId, settingId, skip)

    def GetIndexOf(self, categoryId, settingId, skip=0):
        settingsInCategory = self.__settingsIndex[categoryId]
        if settingsInCategory.count(settingId) == 1:
            return settingsInCategory.index(settingId)

        self.__logger.Warning("Multiple values found for settingId %s, using #%s", settingId, skip)
        settingIndexes = filter(lambda s: s == settingId, settingsInCategory)
        if not settingIndexes:
            raise ValueError("No settings found for %s" % (settingId, ))

        index = 0
        indexStart = 0
        for i in range(0, skip + 1):
            # start one after the current index (but then we need to add +1 to the found index)
            index += settingsInCategory[indexStart:].index(settingId)
            if i > 0:
                index += 1
            indexStart = index + 1
        return index

    # def TransformXml(self):
    #     xml = ElementTree.tostring(self.__template, )

    def Transform(self):
        # we go through it line by line, because we don't want to modify any order in attributes
        # or whitespaces. This currently only works for SINGLE LINE XML elements!
        result = []
        category = None
        settingsInCategory = []
        for line in self.__templateLines:
            # always append the line
            self.__logger.Trace("%s", line.strip())
            result.append(line)

            if "<category" in line:
                line = line.replace(">", "/>")
                element = ElementTree.fromstring(line)
                # we start a new category
                category = element.attrib["id"]
                settingsInCategory = []
                continue

            if not line.strip() or "/>" not in line or line.strip().startswith("<!--"):
                continue

            element = ElementTree.fromstring(line)
            elementId = element.attrib.get("id", ElementTree.tostring(element))

            if category is None:
                # visible only works within categories
                continue

            # so we found an ID of a setting see if it was a duplicate and add it to the items
            # that were found. We need this to support duplicate IDs in the settings within a
            # single category.
            settingIdsFoundBefore = settingsInCategory.count(elementId)
            settingsInCategory.append(elementId)

            # now see if we need to replace
            if "visible" not in element.attrib or "%" not in element.attrib.get("visible", ""):
                # we need a visible attribute with a template
                continue

            self.__logger.Debug("IN:  %s", line.strip())
            matches = self.__relativeRegex.findall(line)
            for match in matches:
                # line = line.replace(match[0], str(self.GetIndexOf(match[1]) - settingIndex))
                line = line.replace(match[0], str(self.GetOffset(category, match[1], elementId, skip=settingIdsFoundBefore)))

            # replace the line we added at the start
            result[-1] = line
            self.__logger.Debug("OUT: %s", line.strip())
        return "".join(result)
