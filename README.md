# Geokodowanie UUG

## PL

Wtyczka QGIS, która umożliwia lokalizację przestrzenną wybranego punktu adresowego, ulicy lub miejscowości. Pobieranie danych jest realizowane przez usługę UUG udostępnianą przez Główny Urząd Geodezji i Kartografii. Obsługuje pliki CSV, które mogą (ale nie muszą) zawierać nagłówki.

### Instrukcja pobrania:
1. Wtyczkę należy zainstalować w QGIS jako ZIP bądź wgrać pliki wtyczki do lokalizacji C:\Users\User\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins.
2. Aby uruchomić wtyczkę, należy kliknąć na ikonę zielonego drzewa.
3. Jeżeli ikona wtyczki nie jest widoczna w panelu warstw, spróbuj zrestartować QGIS.
4. Jeżeli wtyczka nadal nie jest widoczna, należy przejść w QGIS Desktop do Wtyczki -> Zarządzanie wtyczkami -> Zainstalowane -> geokodowanie_uug -> Odinstalować wtyczkę i zainstalować ponownie.

### Instrukcja użytkowania:
* Aby odblokowac przycisk "Geokoduj", należy wybrać dwa pliki: plik z adresami w formacie .csv oraz plik do zapisywania niezgeokodowanych adresów w formacie .txt.
* Przed geokodowaniem warto sprawdzić, czy system kodowania we wtyczce zgadza się z systemem kodowania w pliku z adresami.
* Jeśli zaznaczysz opcję "Pierwszy wiersz zawiera nazwy kolumn", to ten wiersz nie będzie brany pod uwagę podczas geokodowania.
* Wtyczka, w zależności od danych źródłowych i ustaleń użytkownika, może zwracać punkty (budynki, miejscowości), linie (ulice) lub poligony (place).
* Po kliknięciu przycisku "Geokoduj" rozpocznie się proces geokodowania. Indykatorem tego będzie niebieski pasek w dolnej prawej części interfejsu QGIS.
* W zależności od liczby punktów do geokodowania, proces może zająć pewien czas. W takim przypadku wtyczkę można zminimalizować, naciskając przycisk "Zamknij". Proces będzie kontynuowany w tle.
* Proces geokodowania można zatrzymać. W tym celu należy kliknąć na niebieski pasek na dole z prawej strony, wybrać proces "geokodowanie" oraz nacisnąć na pojawiający się krzyżyk.

### Uwaga:
* Warunkiem koniecznym do prawidłowego działania wtyczki jest posiadanie wersji QGIS 3.16.16 lub wyższej.
* Dla niektórych adresów brak jest kodów pocztowych w bazie GUGiK. Należy wtedy użyć 00-000 lub wartości pustej.
* Jeśli usługa zwróci kilka punktów adresowych, wszystkie zostaną dodane do warstw wynikowych.

## EN

The QGIS plugin allows for the spatial location of a selected address point, street, or locality. Data retrieval is carried out through the UUG service provided by the Head Office of Geodesy and Cartography. It supports CSV files. The file may (but does not have to) contain headers.

### Download Instructions
1. The plugin should be installed in QGIS as a ZIP or by uploading the plugin files to the location C:\Users\User\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins.
2. To launch the plugin, click on the icon with a green tree.
3. If the plugin icon is not visible in the layer panel, try restarting QGIS.
4. If the plugin is still not visible, go to QGIS Desktop -> Plugins -> Manage and Install Plugins -> Installed -> geokodowanie_uug -> Uninstall the plugin, and reinstall it.

### Usage Instructions:
* To unlock the "Geokoduj" button, select two files: a file with addresses in .csv format and a file for saving ungeocoded addresses in .txt format.
* Before geocoding, it is worth checking if the encoding system in the plugin matches the encoding system in the address file.
* If you select the option "Pierwszy wiersz zawiera nazwy kolumn", this row will not be considered during geocoding.
* Depending on the source data and user settings, the plugin can return points (buildings, localities), lines (streets), or polygons (squares).
* After clicking the "Geokoduj" button, the geocoding process will start. This will be indicated by a blue bar in the lower right part of the QGIS interface.
* Depending on the number of points to be geocoded, the process may take some time. In such a case, the plugin can be minimized by pressing the "Zamknij" button. The process will continue in the background.
* The geocoding process can be stopped. To do this, click on the blue bar at the bottom right, select the "geokodowanie" process, and click on the appearing cross.

### Note:
* A necessary condition for the proper functioning of the plugin is having QGIS version 3.16.16 or higher.
* For some addresses, postal codes are missing in the GUGiK database. In such cases, use 00-000 or leave the value empty.
* If the service returns multiple address points, all of them will be added to the result layers.

#### Sample geocoding input file/  Przykładowy plik do geokodowania:
```
miasto,ulica,kod,numer
Warszawa, Szeligowska, 01-320, 32A
Marki, Andersa,, 1
Słupno, Lipowa, 09-472, 4
Słupno, Lipowa, 05-250, 4
```
