import urllib.request
import urllib.parse
import json
import re
import logging

from qgis.core import (
    Qgis,
    QgsProject,
    QgsGeometry,
    QgsFeature,
    QgsTask,
    QgsMessageLog
    )
from qgis.gui import QgsMessageBar
from qgis.PyQt.QtCore import QObject, pyqtSignal

class Geokodowanie(QgsTask):
    finishedProcessing = pyqtSignal(list, list)
    def __init__(self, rekordy, miejscowosci, ulicy, numery, delimeter, warstwa, iface):
        
        super().__init__("Geokodowanie", QgsTask.CanCancel)
        self.iface = iface
        self.rekordy = rekordy
        self.miejscowosci = miejscowosci
        self.ulicy = ulicy
        self.numery = numery
        self.delimeter = delimeter
        self.wartswa = warstwa
        self.features = []
        self.bledne = []
        self.iface.messageBar().pushMessage(
            "Info: ", 
            "Zaczął się procej geokodowania.", 
            level=Qgis.Info,
            duration=5
        )

    def run(self):
        total = len(self.rekordy)
        for i, rekord in enumerate(self.rekordy):
          
            wartosci = rekord.strip().split(self.delimeter)
            wkt = self.geocode(self.miejscowosci[i], self.ulicy[i], self.numery[i])
            
            if wkt:
                geom = QgsGeometry().fromWkt(wkt)
                feat = QgsFeature()
                feat.setGeometry(geom)
                feat.setAttributes(wartosci)
                self.features.append(feat)
            else:
                self.bledne.append(self.miejscowosci[i] + self.delimeter + self.ulicy[i] + self.delimeter + self.numery[i] +"\n")

            self.setProgress(self.progress() + 100 / total)
            if self.isCanceled():
                return False
        
        self.finishedProcessing.emit(self.features, self.bledne)
        return True


    def geocode(self, miasto, ulica, numer):
        service = "http://services.gugik.gov.pl/uug/?"
        params = {
            "request": "GetAddress", 
            "address": f"{miasto}, {ulica} {numer}" 
            if ulica and ulica.strip() != miasto.strip() 
            else f"{miasto} {numer}"
        }
        params_url = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        request_url = service + params_url

        try:
            response = urllib.request.urlopen(request_url).read()
        except urllib.error.URLError as e:
            logging.error(f"Connection failed: {e.reason}")
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
        response_json = {}        
        try:
            response_json = json.loads(response.decode('utf-8'))
        except json.JSONDecodeError:
            logging.error("Decoding JSON has failed")

        if "results" not in response_json or not response_json["results"]:
            logging.warning("No results found.")
            return
        else:
            return response_json["results"]["1"]["geometry_wkt"]
            

    def finished(self, result):
        print("koniec?")
        if result:
            QgsMessageLog.logMessage('sukces')
            self.iface.messageBar().pushMessage("Sukces", "Udało się! Dane BDOT10k zostały pobrane.",
                                                level=Qgis.Success, duration=5)
        else:
            self.iface.messageBar().pushMessage("Błąd",
                                                "Geokodowanie  nie powiodło się.", level=Qgis.Warning, duration=5)
            self.finishedProcessing.emit(self.features, self.bledne)

    def cancel(self):
        self.finishedProcessing.emit(self.features, self.bledne)
        super().cancel()