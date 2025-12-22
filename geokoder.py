import json

from qgis.core import (
    Qgis,
    QgsProject,
    QgsGeometry,
    QgsFeature,
    QgsTask,
    QgsWkbTypes
    )
from qgis.PyQt.QtCore import QObject, pyqtSignal
from .utils import QgsTools

class Geokodowanie(QgsTask):
    finishedProcessing = pyqtSignal(list, list, list, list, bool)

    def __init__(self, rekordy, miejscowosci, ulicy, numery, kody, delimeter, iface):
        super().__init__("Geokodowanie", QgsTask.CanCancel)
        self.iface = iface
        self.qgs_tools = QgsTools(self.iface)
        self.rekordy = rekordy
        self.miejscowosci = miejscowosci
        self.ulicy = ulicy
        self.numery = numery
        self.kody = kody
        self.delimeter = delimeter
        self.featuresLine = []

        self.featuresPoly = []
        self.featuresPoint = []
        self.bledne = []
        self.service = GUGIK
        self.iface.messageBar().pushMessage(
            "Info: ", 
            "Zaczął się proces geokodowania.", 
            level=Qgis.Info,
            duration=10
        )

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

        self.qgs_tools.pushLogInfo("Zaczął się proces geokodowania.")

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
                self.qgs_tools.pushLogWarning(msg)
                self.qgs_tools.pushWarning(msg)
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
                self.qgs_tools.pushLogWarning(msg)
                self.qgs_tools.pushWarning(msg)
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
        
        # Kodowanie parametrów zapytania w URL
        params_url = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        request_url = self.service + params_url

        self.qgs_tools.pushLogInfo(f"Wysyłanie zapytania do api: {params}")
        
        try:
            # Wysłanie zapytania do serwera i odczytanie odpowiedzi
            response = urllib.request.urlopen(request_url).read()
            response_json = json.loads(response.decode('utf-8'))
        except urllib.error.URLError as e:
            msg = f"Nie udało się połączyć z usługą API: {e.reason}"
            self.qgs_tools.pushLogWarning(msg)
            return None
        except json.JSONDecodeError:
            msg = "Nie udało się odczytać pliku JSON"
            self.qgs_tools.pushLogCritical(msg)
            return None
        except Exception as e:
            msg = f"Zdarzył się nieoczekiwany błąd: {e}"
            self.qgs_tools.pushLogCritical(msg)
            return None

        if "results" not in response_json or not response_json["results"]:
            msg = "Usługa API nie zwróciła odpowiedzi."
            self.qgs_tools.pushLogWarning(msg)
            return None
        elif response_json["found objects"] > 1:
            for result in response_json["results"]:
                return response_json["results"][f"{result}"]["geometry_wkt"]
        else:
            return response_json["results"]["1"]["geometry_wkt"]

    def finished(self, result):
        if not result and self.stop != True:
            msg = (
                f"Geokodowanie  nie powiodło się."
            )
            self.qgs_tools.pushWarning(msg)
            self.qgs_tools.pushLogWarning(msg)
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
