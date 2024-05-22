import urllib.request
import urllib.parse
import json
import re
import logging
from .geokodowanie_adresow_dialog import GeokodowanieAdresowDialog
from qgis.core import (
    Qgis,
    QgsProject,
    QgsGeometry,
    QgsFeature,
    QgsTask,
    QgsMessageLog,
    QgsWkbTypes
    )
from qgis.gui import QgsMessageBar
from qgis.PyQt.QtCore import QObject, pyqtSignal

class Geokodowanie(QgsTask):
    finishedProcessing = pyqtSignal(list, list, list)
    def __init__(self, rekordy, miejscowosci, ulicy, numery, kody, delimeter, iface):
        super().__init__("Geokodowanie", QgsTask.CanCancel)
        self.iface = iface
        self.rekordy = rekordy
        self.miejscowosci = miejscowosci
        self.ulicy = ulicy
        self.numery = numery
        self.kody = kody
        self.delimeter = delimeter
        self.featuresLine = []
        self.featuresPoint = []
        self.bledne = []
        self.iface.messageBar().pushMessage(
            "Info: ", 
            "Zaczął się procej geokodowania.", 
            level=Qgis.Info,
            duration=10
        )

    def run(self):
        total = len(self.rekordy)
        unique_geometries = set()  # Zbiór do przechowywania unikalnych geometrii jako WKT string
        
        for i, rekord in enumerate(self.rekordy):
            self.kilka = []
            wartosci = rekord.strip().split(self.delimeter)
            wkt = self.geocode(self.miejscowosci[i].strip(), self.ulicy[i].strip(), self.numery[i].strip(), self.kody[i].strip())
            if not wkt:
                wkt = self.geocode(self.miejscowosci[i].strip(), self.ulicy[i].strip(), self.numery[i].strip(), "")
            if not wkt:
                self.bledne.append(f"{self.miejscowosci[i]}{self.delimeter}{self.ulicy[i]}{self.delimeter}{self.numery[i]}{self.delimeter}{self.kody[i]}\n")
            else:
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
                        unique_geometries.add(geom_wkt)

            self.setProgress(self.progress() + 100 / total)
            if self.isCanceled():
                return False
            
        self.finishedProcessing.emit(self.featuresPoint, self.featuresLine, self.bledne)
        return True



    def geocode(self, miasto, ulica, numer, kod):
        service = "http://services.gugik.gov.pl/uug/?"
        params = {"request": "GetAddress"}
        
        if ulica and ulica.strip() == miasto.strip() or not ulica and numer:
            params["address"] = f"{kod} {miasto}, {numer}"
        elif not ulica or ulica == "":
            params["address"] = f"{miasto}"
        elif not numer or numer == "":
            params["address"] = f"{miasto}, {ulica}"
        else:
            params["address"] = f"{kod} {miasto}, {ulica} {numer}"
        
        params_url = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        request_url = service + params_url
        print(request_url)
        
        try:
            response = urllib.request.urlopen(request_url).read()
            response_json = json.loads(response.decode('utf-8'))
        except urllib.error.URLError as e:
            logging.error(f"Connection failed: {e.reason}")
            return None
        except json.JSONDecodeError:
            logging.error("Decoding JSON has failed")
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return None

        if "results" not in response_json or not response_json["results"]:
            logging.warning("No results found.")
            return None
        elif response_json["found objects"] > 1:
            return [response_json["results"][f"{result}"]["geometry_wkt"] for result in response_json["results"]]
        else:
            return response_json["results"]["1"]["geometry_wkt"]
            

    def finished(self, result):
        if not result:
            self.iface.messageBar().pushMessage(
                "Błąd","Geokodowanie  nie powiodło się.",
                  level=Qgis.Warning,
                    duration=10
            )
            self.finishedProcessing.emit(self.featuresPoint, self.featuresLine, self.bledne)

    def cancel(self):
        self.finishedProcessing.emit(self.featuresPoint, self.featuresLine, self.bledne)
        super().cancel()
