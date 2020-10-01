import urllib.request
import urllib.parse
import json


def geocode(miasto, ulica, numer, kod):
    service = "http://services.gugik.gov.pl/uug/?"
    if ulica.strip() == '' or ulica.strip() == miasto.strip():
        params = {"request": "GetAddress", "address": "%s %s %s" % (kod, miasto, numer)}
    else:
        params = {"request":"GetAddress", "address":"%s %s, %s %s" % (kod, miasto, ulica, numer)}
    paramsUrl = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    request = urllib.request.Request(service + paramsUrl)
    print(service + paramsUrl)
    response = urllib.request.urlopen(request).read()
    js = response.decode("utf-8") #pobrany, zdekodowany plik json z odpowiedzia z serwera
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


if __name__ == '__main__':
    g = geocode(miasto='Słupno', ulica='Lipowa', numer='4', kod='09-472')
    print(g)
    g = geocode(miasto='Słupno', ulica='Lipowa', numer='4', kod='05-250')
    print(g)
    g = geocode(miasto='Słupno', ulica='Lipowa', numer='4', kod='')
    print(g)
    g = geocode(miasto='Opole', ulica='Opolska', numer='34', kod='45-960')
    print(g)
    g = geocode(miasto='Opole', ulica='Edmunda Osmańczyka', numer='20', kod='45-027')
    print(g)