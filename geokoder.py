import urllib.request
import urllib.parse
import json

def geocode(miasto, ulica, numer, kod):
    service = "http://services.gugik.gov.pl/uug/?"
    params = {"request":"GetAddress", "address":"%s %s, %s %s" % (kod, miasto, ulica, numer)}
    paramsUrl = urllib.parse.urlencode(params, quote_via=urllib.parse.quote_plus)
    request = urllib.request.Request(service + paramsUrl)
    # print(service + paramsUrl)
    response = urllib.request.urlopen(request).read()
    js = response.decode("utf-8") #pobrany, zdekodowany plik json z odpowiedzia z serwera
    w = json.loads(js)

    try:
        results = w['results']
        if not results: #jeżeli jest pusta lista z wynikami
            return None
        else: #jeżeli są wyniki
            geomWkt = w['results']["1"]['geometry_wkt'] #weź pierwszy wynik z odpowiedzi serwera
            return geomWkt
    except KeyError:
        print(w)
        return (str(w),0)

# print(geocode("Warszawa", "Szeligowska", "32A", "01-320"))