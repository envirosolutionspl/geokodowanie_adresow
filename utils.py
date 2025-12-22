from qgis._core import QgsMessageLog, Qgis
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.PyQt.QtGui import QIcon

from . import PLUGIN_NAME

class QgsTools:

    default_tag = PLUGIN_NAME

    def __init__(self, iface):
        self.iface = iface

    def pushSuccess(self, message: str) -> None:
        self.iface.messageBar().pushMessage(
            'Sukces',
            message,
            level=Qgis.Success,
            duration=10
        )

    def pushMessage(self, message: str) -> None:
        self.iface.messageBar().pushMessage(
            'Informacja',
            message,
            level=Qgis.Info,
            duration=10
        )

    def pushWarning(self, message: str) -> None:
        self.iface.messageBar().pushMessage(
            'Ostrzeżenie',
            message,
            level=Qgis.Warning,
            duration=10
        )

    def pushCritical(self, message: str) -> None:
        self.iface.messageBar().pushMessage(
            'Błąd',
            message,
            level=Qgis.Critical,
            duration=10
        )
    @staticmethod
    def pushLogInfo(message: str) -> None:
        QgsMessageLog.logMessage(message, tag=QgsTools.default_tag, level=Qgis.Info)

    @staticmethod
    def pushLogWarning(message: str) -> None:
        QgsMessageLog.logMessage(message, tag=QgsTools.default_tag, level=Qgis.Warning)

    @staticmethod
    def pushLogCritical(message: str) -> None:
        QgsMessageLog.logMessage(message, tag=QgsTools.default_tag, level=Qgis.Critical)

    @staticmethod
    def pushLogSuccess(message: str) -> None:
        QgsMessageLog.logMessage(message, tag=QgsTools.default_tag, level=Qgis.Success)
