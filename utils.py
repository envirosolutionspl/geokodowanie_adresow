import os
from qgis.core import QgsApplication, QgsMessageLog, Qgis
from qgis.PyQt.QtNetwork import QNetworkRequest, QNetworkReply
from qgis.PyQt.QtCore import QEventLoop, Qt
from qgis.PyQt.QtGui import QIcon, QPainter, QPalette, QPixmap
from qgis.PyQt.QtWidgets import QDialog, QWidget
from . import PLUGIN_NAME

PLUGIN_DIR = os.path.dirname(__file__)


class NotifyTools:

    def __init__(self, iface):
        self.iface = iface

    def pushSuccess(self, message: str) -> None:
        self.iface.messageBar().pushMessage(
            'Sukces',
            message,
            level=Qgis.MessageLevel.Success,
            duration=10
        )

    def pushMessage(self, message: str) -> None:
        self.iface.messageBar().pushMessage(
            'Informacja',
            message,
            level=Qgis.MessageLevel.Info,
            duration=10
        )

    def pushWarning(self, message: str) -> None:
        self.iface.messageBar().pushMessage(
            'Ostrzeżenie',
            message,
            level=Qgis.MessageLevel.Warning,
            duration=10
        )

    def pushCritical(self, message: str) -> None:
        self.iface.messageBar().pushMessage(
            'Błąd',
            message,
            level=Qgis.MessageLevel.Critical,
            duration=10
        )
    
    @staticmethod
    def pushLogInfo(message: str) -> None:
        QgsMessageLog.logMessage(message, tag=PLUGIN_NAME, level=Qgis.MessageLevel.Info)

    @staticmethod
    def pushLogWarning(message: str) -> None:
        QgsMessageLog.logMessage(message, tag=PLUGIN_NAME, level=Qgis.MessageLevel.Warning)

    @staticmethod
    def pushLogCritical(message: str) -> None:
        QgsMessageLog.logMessage(message, tag=PLUGIN_NAME, level=Qgis.MessageLevel.Critical)

    @staticmethod
    def pushLogSuccess(message: str) -> None:
        QgsMessageLog.logMessage(message, tag=PLUGIN_NAME, level=Qgis.MessageLevel.Success)


class NetworkTools:

    @staticmethod
    def getUAHeader():
        return QNetworkRequest.KnownHeaders.UserAgentHeader  # Qt6

    @staticmethod
    def getNetworkNoError():
        return QNetworkReply.NetworkError.NoError
    
    @staticmethod
    def getHttpStatusAttr():
        return QNetworkRequest.Attribute.HttpStatusCodeAttribute


    @staticmethod
    def patchQtCompatibility():
        """ Naprawia exec w QT5/QT6 """
        classes_to_patch = [QEventLoop, QDialog]
        for cls in classes_to_patch:
            if not hasattr(cls, 'exec'):
                cls.exec = cls.exec_

class ThemeUtils:
    """
    Motyw jasny/ciemny i logo dla okna wtyczki
    """

    @staticmethod
    def isDarkTheme():
        """
        Ciemny motyw QGIS (np. Night Mapping) albo ciemna paleta systemu
        """
        name = ''
        try:
            name = (QgsApplication.themeName() or '').lower()
        except AttributeError as e:
            NotifyTools.pushLogCritical(f"Atrybut motywu jest niedostępny (AttributeError): {e}")
        except RuntimeError as e:
            NotifyTools.pushLogCritical(f"Aplikacja QGIS nie jest w pełni zainicjalizowana (RuntimeError): {e}")
        except TypeError as e:
            NotifyTools.pushLogCritical(f"Nieoczekiwany typ danych przy pobieraniu motywu (TypeError): {e}")
        except Exception as e:
            NotifyTools.pushLogCritical(f"Nieoczekiwany błąd: {e}")

        if 'night' in name or 'dark' in name:
            return True
        return QgsApplication.palette().color(QPalette.ColorRole.Window).lightness() < 128

    @staticmethod
    def repolishAll(window):
        for widget in [window] + window.findChildren(QWidget):
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()

    @staticmethod
    def themedIcon(path, size=48, disabled_opacity=0.35):
        icon = QIcon(path)
        dimmed = QPixmap(size, size)
        dimmed.fill(Qt.GlobalColor.transparent)
        painter = QPainter(dimmed)
        painter.setOpacity(disabled_opacity)
        painter.drawPixmap(0, 0, icon.pixmap(size, size))
        painter.end()
        icon.addPixmap(dimmed, QIcon.Mode.Disabled)
        return icon

    @staticmethod
    def setLogo(label, filename, height):
        pix = QPixmap(os.path.join(PLUGIN_DIR, 'images', filename))
        if pix.isNull():
            return
        dpr = label.devicePixelRatioF()
        pix = pix.scaledToHeight(int(height * dpr), Qt.TransformationMode.SmoothTransformation)
        pix.setDevicePixelRatio(dpr)
        label.setScaledContents(False)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setPixmap(pix)
