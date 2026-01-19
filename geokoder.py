import json
from qgis.PyQt.QtCore import QUrl, QUrlQuery, QEventLoop, pyqtSignal
from qgis.PyQt.QtNetwork import QNetworkRequest, QNetworkReply
from qgis.PyQt.QtWidgets import QDialog
from qgis.core import (
    Qgis,
    QgsProject,
    QgsGeometry,
    QgsFeature,
    QgsTask,
    QgsWkbTypes
    )
from .utils import NotifyTools
from .constants import GUGIK, PARAMS

if not hasattr(QDialog, 'exec'):
    QDialog.exec = QDialog.exec_

class Geokodowanie(QgsTask):
    finishedProcessing = pyqtSignal(list, list, list, list, bool)

    def __init__(self, parent, rekordy, miejscowosci, ulicy, numery, kody, delimeter, iface):
        super().__init__("Geokodowanie", QgsTask.CanCancel)
        self.iface = iface
        self.parent = parent
        self.notify_tools = NotifyTools(self.iface)
        self.network_manager = self.parent.network_manager
        self.rekordy = rekordy
        self.miejscowosci = miejscowosci
        self.ulicy = ulicy
        self.numery = numery
        self.kody = kody
        self.delimeter = delimeter
        self.stop = False
        self.featuresLine = []

        self.featuresPoly = []
        self.featuresPoint = []
        self.bledne = []
        self.service = GUGIK


    def run(self):
        """
        Funkcja przetwarza rekordy, wykonując geokodowanie dla każdej pozycji,
        tworzy unikalne obiekty geometrii i dzieli je na punkty oraz linie.
        
        Zwraca:
            bool: True, jeśli przetwarzanie zakończyło się sukcesem, 
            False w przypadku anulowania.
        """

        total = len(self.rekordy)
        unique_geometries = set()  # Zbiór do przechowywania unikalnych geometrii jako WKT string

        self.notify_tools.pushLogInfo("Rozpoczęto proces geokodowania.")

        for i, rekord in enumerate(self.rekordy):
            self.kilka = []
            wartosci = rekord.strip().split(self.delimeter)
            miasto = self.miejscowosci[i].strip()
            ulica = self.ulicy[i].strip()
            numer = self.numery[i].strip()
            kod = self.kody[i].strip()
            geocode_params = [
                (miasto, ulica, numer, kod),
                (miasto, ulica, numer, "")
            ]
            wkt = None
            for params in geocode_params:
                wkt = self.geocode(*params)
                if wkt:
                    break
                
            # Jeżeli nie zwraca wyniku dodaje błąd
            if not wkt:
                self.bledne.append(f"{self.miejscowosci[i]}{self.delimeter}{self.ulicy[i]}{self.delimeter}{self.numery[i]}{self.delimeter}{self.kody[i]}\n")
                msg = (
                    "Nie udało się geokodowanie adresu"
                    f"{self.miejscowosci[i]} {self.ulicy[i]} "
                    f"{self.numery[i]} {self.kody[i]}\n"
                )
                self.notify_tools.pushLogWarning(msg)
                self.notify_tools.pushWarning(msg)
            else:
                # Jeśli wynik geokodowania jest listą geometrii,
                # przetwórz każdą geometrię osobno
                geometries = wkt if isinstance(wkt, list) else [wkt]
                for geom_wkt in geometries:
                    if geom_wkt not in unique_geometries:
                        geom = QgsGeometry().fromWkt(geom_wkt)
                        feat = QgsFeature()
                        feat.setGeometry(geom)
                        feat.setAttributes(wartosci)
                        geometry_type = feat.geometry().type()
                        if geometry_type == QgsWkbTypes.PointGeometry:
                            self.featuresPoint.append(feat)
                        elif geometry_type == QgsWkbTypes.LineGeometry:
                            self.featuresLine.append(feat)
                        elif geometry_type == QgsWkbTypes.PolygonGeometry:
                            self.featuresPoly.append(feat)
                        unique_geometries.add(geom_wkt)

            self.setProgress(self.progress() + 100 / total)

            if self.isCanceled():
                self.stop = True
                msg = "Geokodowanie zostało anulowane"
                self.notify_tools.pushLogWarning(msg)
                self.notify_tools.pushWarning(msg)
                return False
            
        self.finishedProcessing.emit(
            self.featuresPoint, 
            self.featuresLine, 
            self.featuresPoly, 
            self.bledne, 
            False
        )
        return True


    def geocode(self, miasto, ulica, numer, kod):
        """
        Funkcja wykonuje geokodowanie adresu korzystając z usługi GUGiK. 
        Przyjmuje parametry miasta, ulicy, numeru oraz kodu pocztowego.
        
        Returns:
            str: Geometria w formacie WKT (Well-Known Text) lub lista 
            geometrii WKT, jeśli znaleziono więcej niż jeden wynik.
        """

        params = PARAMS.copy()
        if (ulica and ulica.strip() == miasto.strip()) or (not ulica and numer):
            params["address"] = f"{kod} {miasto}, {numer}"
        elif not ulica or ulica == "": 
            params["address"] = f"{miasto}"
        elif not numer or numer == "":
            params["address"] = f"{miasto}, {ulica}"
        else:
            params["address"] = f"{kod} {miasto}, {ulica} {numer}"
        
        # Konfiguracja zapytania QNetworkAccessManager
        url = QUrl(self.service)
        query = QUrlQuery()
        for key, value in params.items():
            query.addQueryItem(key, value)
        url.setQuery(query)

        request = QNetworkRequest(url)
        reply = self.network_manager.get(request)

        msg = (
            f"Geokodowanie adresu {params}"
        )
        self.notify_tools.pushLogInfo(msg)

        loop = QEventLoop()
        reply.finished.connect(loop.quit)
        loop.exec()

        try:
            # Sprawdzenie czy zapytanie się nie powiodło
            if reply.error() != QNetworkReply.NetworkError.NoError:
                msg = (
                    f"Nie udało się połączyć z usługą API."
                )
                self.notify_tools.pushLogWarning(msg)
                self.notify_tools.pushWarning(msg)
                return None

            response_bytes = reply.readAll().data()
            response_json = json.loads(response_bytes.decode('utf-8'))
            
            if "results" not in response_json or not response_json["results"]:
                return None

            results = response_json["results"]
            wkt_list = []

            for key in results:
                wkt = results[key].get("geometry_wkt")
                if wkt:
                    wkt_list.append(wkt)

            if not wkt_list:
                msg = (
                    f"Nie udało się znaleźć geokodowania adresu."
                )
                self.notify_tools.pushLogWarning(msg)
                self.notify_tools.pushWarning(msg)
                return None

            # ZWRACAMY WKT
            return wkt_list if len(wkt_list) > 1 else wkt_list[0]

        except (json.JSONDecodeError, Exception):
            msg = (
                f"Nie udało się znaleźć geokodowania adresu."
            )
            self.notify_tools.pushLogWarning(msg)
            self.notify_tools.pushWarning(msg)
            return None
        finally:
            reply.deleteLater()

    def finished(self, result):
        if not result and self.stop != True:
            msg = (
                f"Geokodowanie  nie powiodło się."
            )
            self.notify_tools.pushWarning(msg)
            self.notify_tools.pushLogWarning(msg)
            self.finishedProcessing.emit(
                self.featuresPoint, 
                self.featuresLine, 
                self.featuresPoly, 
                self.bledne, 
                False
            )

    def cancel(self):
        self.stop = True
        self.finishedProcessing.emit(
            self.featuresPoint, 
            self.featuresLine, 
            self.featuresPoly, 
            self.bledne, 
            self.stop
        )
        super().cancel()
