import urllib.request
import urllib.parse
import json

from qgis.core import (
    Qgis,
    QgsProject)
from qgis.gui import QgsMessageBar

class Geokodowanie:
    def __init__(self, iface):
        self.iface = iface


    def geocode(self, miasto, ulica, numer, kod, kodowanie):
        service = "http://services.gugik.gov.pl/uug/?"
        if ulica.strip() == '' or ulica.strip() == miasto.strip():
            params = {"request": "GetAddress", "address": "%s %s %s" % (kod, miasto, numer)}
        else:
            params = {"request":"GetAddress", "address":"%s %s, %s %s" % (kod, miasto, ulica, numer)}
        paramsUrl = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
        request = urllib.request.Request(service + paramsUrl)
        print(service + paramsUrl)
        response = urllib.request.urlopen(request).read()
        print("Odpowiedz ", response)
        js = response.decode("utf-8")
        print(js)#pobrany, zdekodowany plik json z odpowiedzia z serwera
        if "Blad" in js and "zapytania" in js:
            self.iface.messageBar().pushMessage(
                    "Błąd: ",
                    "Błędne zapytanie do serwera. Proszę sprawdzić system kodowania.",
                    level=Qgis.Critical,
                    duration=6,
                )
        else:
            w = json.loads(js)
            try:
                results = w['results']
                if not results: #jeżeli jest pusta lista z wynikami
                    return None
                else: #zwróć pierwszy wynik
                    geomWkt = w['results']["1"]['geometry_wkt'] #weź pierwszy wynik z odpowiedzi serwera
                    return geomWkt
            except KeyError:
                print(w)
                return (str(w),0)


    # if __name__ == '__main__':
    #     g = geocode(miasto='Słupno', ulica='Lipowa', numer='4', kod='09-472')
    #     print(g)
    #     g = geocode(miasto='Słupno', ulica='Lipowa', numer='4', kod='05-250')
    #     print(g)
    #     g = geocode(miasto='Słupno', ulica='Lipowa', numer='4', kod='')
    #     print(g)
    #     g = geocode(miasto='Opole', ulica='Opolska', numer='34', kod='45-960')
    #     print(g)
    #     g = geocode(miasto='Opole', ulica='Edmunda Osmańczyka', numer='20', kod='45-027')
    #     print(g)