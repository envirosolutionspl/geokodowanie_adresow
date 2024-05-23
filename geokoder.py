import urllib.request
import urllib.parse
import json
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
    finishedProcessing = pyqtSignal(list, list, list, bool)
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
        self.stop = False
        
        self.iface.messageBar().pushMessage(
            "Info: ", 
            "Zaczął się procej geokodowania.", 
            level=Qgis.Info,
            duration=10
        )

    def run(self):
        """
        Funkcja przetwarza rekordy, wykonując geokodowanie dla każdej pozycji,
        tworzy unikalne obiekty geometrii i dzieli je na punkty oraz linie.
        
        Zwraca:
            bool: True, jeśli przetwarzanie zakończyło się sukcesem, False w przypadku anulowania.
        """
        total = len(self.rekordy)
        unique_geometries = set()  # Zbiór do przechowywania unikalnych geometrii jako WKT string
        QgsMessageLog.logMessage("Zaczął się proces geokodowania.")
        for i, rekord in enumerate(self.rekordy):
            self.kilka = []
            # Rozdzielenie rekordu na wartości
            wartosci = rekord.strip().split(self.delimeter)
            # Geokodowanie adresu
            wkt = self.geocode(self.miejscowosci[i].strip(), self.ulicy[i].strip(), self.numery[i].strip(), self.kody[i].strip())
            
            # Jeśli pierwsze geokodowanie nie zwróci wyniku, próbuj bez kodu pocztowego
            if not wkt:
                wkt = self.geocode(self.miejscowosci[i].strip(), self.ulicy[i].strip(), self.numery[i].strip(), "")
            
            # Jeśli geokodowanie nie zwróci wyniku, dodaj rekord do listy błędów
            if not wkt:
                self.bledne.append(f"{self.miejscowosci[i]}{self.delimeter}{self.ulicy[i]}{self.delimeter}{self.numery[i]}{self.delimeter}{self.kody[i]}\n")
            else:
                # Jeśli wynik geokodowania jest listą geometrii, przetwórz każdą geometrię osobno
                geometries = wkt if isinstance(wkt, list) else [wkt]
                for geom_wkt in geometries:
                    if geom_wkt not in unique_geometries:
                        # Tworzenie obiektu QgsGeometry z WKT
                        geom = QgsGeometry().fromWkt(geom_wkt)
                        feat = QgsFeature()
                        feat.setGeometry(geom)
                        feat.setAttributes(wartosci)
                        geometry_type = feat.geometry().type()
                        # Dodawanie obiektów do odpowiednich list w zależności od typu geometrii
                        if geometry_type == QgsWkbTypes.PointGeometry:
                            self.featuresPoint.append(feat)
                        elif geometry_type == QgsWkbTypes.LineGeometry:
                            self.featuresLine.append(feat)
                        # Dodanie geometrii do zbioru unikalnych geometrii
                        unique_geometries.add(geom_wkt)

            # Ustawianie postępu zadania
            self.setProgress(self.progress() + 100 / total)
            # Sprawdzenie, czy zadanie zostało anulowane
            if self.isCanceled():
                self.stop = True
                return False
            
        # Emitowanie sygnału zakończenia przetwarzania
        self.finishedProcessing.emit(self.featuresPoint, self.featuresLine, self.bledne, False)
        return True



    def geocode(self, miasto, ulica, numer, kod):
        """
        Funkcja wykonuje geokodowanie adresu korzystając z usługi GUGiK. 
        Przyjmuje parametry miasta, ulicy, numeru oraz kodu pocztowego.
        
        Returns:
            str: Geometria w formacie WKT (Well-Known Text) lub lista geometrii WKT, jeśli znaleziono więcej niż jeden wynik.
        """
        
        service = "http://services.gugik.gov.pl/uug/?"  # Adres usługi geokodowania GUGiK
        params = {"request": "GetAddress"}  # Parametry zapytania

        # Ustalenie parametru "address" w zależności od dostępnych danych adresowych
        if ulica and ulica.strip() == miasto.strip() or not ulica and numer:
            params["address"] = f"{kod} {miasto}, {numer}"
        elif not ulica or ulica == "": 
            params["address"] = f"{miasto}"
        elif not numer or numer == "":
            params["address"] = f"{miasto}, {ulica}"
        else:
            params["address"] = f"{kod} {miasto}, {ulica} {numer}"
        
        # Kodowanie parametrów zapytania w URL
        params_url = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        request_url = service + params_url
        QgsMessageLog.logMessage(f"Wysyłanie zapytania do api: {params}")
        
        try:
            # Wysłanie zapytania do serwera i odczytanie odpowiedzi
            response = urllib.request.urlopen(request_url).read()
            response_json = json.loads(response.decode('utf-8'))
        except urllib.error.URLError as e:
            QgsMessageLog.logMessage(f"Nie udało się połączyć z usługą API: {e.reason}")
            return None
        except json.JSONDecodeError:
            QgsMessageLog.logMessage("Nie udało się odczytać pliku JSON")
            return None
        except Exception as e:
            QgsMessageLog.logMessage(f"Zdarzył się nieoczekiwany błąd: {e}")
            return None

        # Sprawdzenie czy odpowiedź zawiera wyniki
        if "results" not in response_json or not response_json["results"]:
            QgsMessageLog.logMessage("Usługa API nie zwróciła odpowiedzi.")
            return None
        # Jeśli znaleziono więcej niż jeden wynik, zwróć listę geometrii WKT
        elif response_json["found objects"] > 1:
            return [response_json["results"][f"{result}"]["geometry_wkt"] for result in response_json["results"]]
        # W przeciwnym razie, zwróć pojedynczą geometrię WKT
        else:
            return response_json["results"]["1"]["geometry_wkt"]
                

    def finished(self, result):
        if not result and self.stop != True:
            self.iface.messageBar().pushMessage(
              "Błąd","Geokodowanie  nie powiodło się.",
              level=Qgis.Warning,
              duration=10
            )
            self.finishedProcessing.emit(self.featuresPoint, self.featuresLine, self.bledne, False)

    def cancel(self):
        self.stop = True
        self.finishedProcessing.emit(self.featuresPoint, self.featuresLine, self.bledne, self.stop)
        super().cancel()
