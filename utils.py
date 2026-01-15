from qgis._core import QgsMessageLog, Qgis
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtNetwork import QNetworkRequest, QNetworkReply
from qgis.PyQt.QtCore import QEventLoop
from qgis.PyQt.QtWidgets import QDialog

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

    # --- HELPERY DLA Qt5 / Qt6 ---

    @staticmethod
    def getUAHeader():
        """Zwraca UserAgentHeader dla Qt5/Qt6."""
        if hasattr(QNetworkRequest, 'KnownHeaders'):
            return QNetworkRequest.KnownHeaders.UserAgentHeader # Qt6
        return QNetworkRequest.UserAgentHeader # Qt5

    @staticmethod
    def getNetworkNoError():
        """Zwraca NetworkNoError dla Qt5/Qt6."""
        if hasattr(QNetworkReply, 'NetworkError'):
            return QNetworkReply.NetworkError.NoError # Qt6
        return QNetworkReply.NoError # Qt5
    
    @staticmethod
    def getHttpStatusAttr():
        """Zwraca HttpStatusCodeAttribute dla Qt5/Qt6."""
        if hasattr(QNetworkRequest, 'Attribute'):
            return QNetworkRequest.Attribute.HttpStatusCodeAttribute # Qt6
        return QNetworkRequest.HttpStatusCodeAttribute # Qt5

    @staticmethod
    def patchQtCompatibility():
        """ Naprawia exec w QT5/QT6 """
        classes_to_patch = [QEventLoop, QDialog]
        for cls in classes_to_patch:
            if not hasattr(cls, 'exec'):
                cls.exec = cls.exec_
