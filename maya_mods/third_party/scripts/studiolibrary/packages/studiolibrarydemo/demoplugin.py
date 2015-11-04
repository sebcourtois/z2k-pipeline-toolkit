#!/usr/bin/python
"""
To test this demo please run this file. You don't need to be in Maya to
run this demo.

The Studio Library window:

    |+=================x|
    |     |R|R|R|R|     |
    |  F  |R|R    | C/P |
    |     |       |     |
    |     |       |     |
    |-------------------|

F = FolderWidget
The folder widget should not be modified by the plugin

R = Record
A record is an individual item which you can save and load data from.
If you would like to customize the behaviour of a record you will need to
inherit from studiolibrary.Record (see the atom plugin for more details).
It should also be possible to load a record in gui mode or in batch mode.

C = CreateWidget
The create widget is a normal Qt Widget that will be passed the Record
object for saving.

P = PreviewWidget
The preview widget is a normal Qt Widget that will be passed the selected
Record for loading.
"""
import logging
import studiolibrary

from PySide import QtGui
from PySide import QtCore


__all__ = ["Plugin"]
logger = logging.getLogger(__name__)


class Plugin(studiolibrary.Plugin):
    """
    A studio library plugin must have a Plugin class as the main entry point.
    """

    def __init__(self, library):
        """
        :type library: studiolibrary.Library
        """
        studiolibrary.Plugin.__init__(self, library)

        self.setName("Demo")
        self.setExtension("demo")
        self.setIconPath(self.dirname() + "/resource/images/demo.png")

        self.setRecord(Record)
        self.setCreateWidget(CreateWidget)
        self.setPreviewWidget(PreviewWidget)

        # Use the settings object on the plugin class for
        # custom plugin options.
        # eg: "paste option", "current time",
        settings = self.settings()
        settings.setdefault("customPluginOption", True)


class Record(studiolibrary.Record):

    def __init__(self, *args, **kwargs):
        """
        """
        studiolibrary.Record.__init__(self, *args, **kwargs)

    def doubleClicked(self):
        """
        """
        self.load()

    def save(self, path, contents=None, force=False):
        """
        Add custom saving methods here
        """
        logger.info("Saving a new record!!")
        self.metaFile().data().setdefault("customRecordOption", "Hello World")
        studiolibrary.Record.save(self, path=path, contents=contents, force=force)

    def load(self):
        """
        Add custom loading methods here
        """
        logger.info('----------------')
        logger.info('Loading record "%s"' % self.path())
        logger.info('Record Option: %s' % self.metaFile().data().get("customRecordOption"))
        logger.info('Plugin Option: %s' % self.plugin().settings().get("customPluginOption"))
        logger.info('Record: %s' % self)
        logger.info('Loaded record!')
        logger.info('----------------')


class CreateWidget(QtGui.QWidget):
    """
    If you're using studiolibrary.loadUi() then the ui file
    must have the following naming convention /resource/ui/CreateWidget.ui
    """

    def __init__(self, record, libraryWidget=None):
        """
        :type record: Record
        :type libraryWidget: studiolibrary.LibraryWidget
        """
        QtGui.QWidget.__init__(self, None)
        studiolibrary.loadUi(self)

        self._record = record
        self._libraryWidget = libraryWidget

        self.connect(self.ui.acceptButton, QtCore.SIGNAL("clicked()"), self.accept)

    def record(self):
        """
        :rtype: Record
        """
        return self._record

    def libraryWidget(self):
        """
        :rtype: studiolibrary.LibraryWidget
        """
        return self._libraryWidget

    def showEvent(self, event):
        """
        :type: QtGui.Event
        """
        QtGui.QWidget.showEvent(self, event)
        self.ui.name.setFocus()

    def accept(self):
        """
        :rtype: None
        """
        try:
            folder = self.libraryWidget().selectedFolder()
            if not folder:
                raise Exception("No folder selected. Please select a destination folder.")

            path = folder.path() + "/" + str(self.ui.name.text())
            description = str(self.ui.description.toPlainText())

            r = self.record()
            r.setDescription(description)
            r.save(path=path)

        except Exception, msg:
            import traceback
            traceback.print_exc()
            self.libraryWidget().criticalDialog(str(msg))


class PreviewWidget(QtGui.QWidget):
    """
    If you're using studiolibrary.loadUi() then the ui file
    must have the following naming convention /resource/ui/PreviewWidget.ui
    """

    def __init__(self, record, libraryWidget=None):
        """
        :type record: Record
        :type libraryWidget: studiolibrary.LibraryWidget
        """
        QtGui.QWidget.__init__(self, libraryWidget)
        studiolibrary.loadUi(self)

        self._record = record
        self._libraryWidget = libraryWidget

        self.ui.name.setText(self.record().name())
        self.ui.description.setPlainText(self.record().description())
        self.ui.optionCheckBox.setChecked(self.settings().get("customPluginOption"))

        self.connect(self.ui.acceptButton, QtCore.SIGNAL("clicked()"), self.accept)
        self.connect(self.ui.optionCheckBox, QtCore.SIGNAL("stateChanged(int)"), self.optionChanged)

    def record(self):
        """
        :rtype: Record
        """
        return self._record

    def libraryWidget(self):
        """
        :rtype: studiolibrary.LibraryWidget
        """
        return self._libraryWidget

    def settings(self):
        """
        :rtype: studiolibrary.Settings
        """
        return self.record().plugin().settings()

    def optionChanged(self, value):
        """
        :type value: int
        """
        self.settings().set("customPluginOption", value)
        self.settings().save()

    def accept(self):
        """
        """
        self.record().load()
        msg = "You have successfully tested the demo plugin!\nRecord Object:\n%s" % self.record()
        self.libraryWidget().informationDialog(msg)


def test():
    """
    :rtype: None
    """
    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)s: %(funcName)s: %(message)s')

    import studiolibrary
    logging.info("Plugin Path:", __file__)
    studiolibrary.main(name="Demo", plugins=[__file__])


if __name__ == "__main__":
    test()
