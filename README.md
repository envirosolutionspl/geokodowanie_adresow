# Geokodowanie UUG

## PL

Wtyczka Qgis, która umożliwia lokalizację przestrzenną wybranego punktu adresowego, ulicy lub miejscowości. Pobieranie danych jest realizowane przez usługę UUG udostępnianą przez Główny Urząd Geodezji i Kartografii. Obsługuje pliki CSV. Plik może (ale nie musi) zawierać nagłówki.

### Instrukcja pobrania
1. Wtyczkę należy zainstalować w QGISie jako ZIP bądź wgrać pliki wtyczki do lokalizacji C:\Users\User\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins.
2. Aby uruchomić wtyczkę należy kliknąć na ikonę zielonego drzewa oznaczonego napisem ULDK.
3. Jeżeli ikona wtyczki nie jest widoczna w panelu warstw, spróbuj zrestartować QGIS.
4. Jeżeli wtyczka nadal nie jest widoczna  należy przejść w QGIS Desktop do Wtyczki -> Zarządzanie wtyczkami -> Zainstalowane -> geokodowanie_uug -> Odinstalować wtyczkę, i zainstalować ponownie.<br>

### Instrukcja użytkowania:
* Aby uruchomić proces geokodowania, należy wybrać dwa pliki: plik z adresami w formacie .csv oraz plik do zapisywania niezgeokodowanych adresów w formacie .txt.
* Przed geokodowaniem warto sprawdzić, czy system kodowania we wtyczce zgadza się z systemem kodowania w pliku z adresami.
* Jeśli zaznaczysz opcję "Pierwszy wiersz zawiera nazwy kolumn", to ten wiersz nie będzie brany pod uwagę podczas geokodowania.
* Wtyczka, w zależności od danych źródłowych i ustaleń użytkownika, może zwracać punkty (budynki, miejscowości), linie (ulice) lub poligony (place).

### Uwaga:
* Warunkiem koniecznym do prawidłowego działania wtyczki jest posiadanie wersji QGIS 3.16.16 lub wyższej.
* Dla niektórych adresów brak jest kodów pocztowych w bazie GUGiK. Należy wtedy użyć 00-000 lub wartości pustej.
* Jeśli usługa zwróci kilka punktów adresowych, wszystkie zostaną dodane do warstw wynikowych.

## changelog
  Version 1.1.3
  * wyszukuje adresy 'wiejskie' gdy nazwa ulicy jest pusta lub taka jak miejscowość
  
  Version 1.1.2
  * dodanie wszystkich pól z pliku wejściowego w warstwie wynikowej
  * sprawdzanie całego pliku z adresami przed rozpoczeciem geokodowania
  * dodanie komunikatów o błędach w pliku wejściowym
  * poprawa geokodowania plików bez nagłówków
  
  Version 1.1.1
  * poprawy błędów
  * rozwinięcie skrótów al. i pl. w nazwach ulic w celu zwiększenia skuteczności
  
  Version 1.1.0
  * dodanie możliwości definicji separatora kolumn
  * poprawy błędów

## EN
EN: QGIS 3 Plugin for geocoding addresses of Poland from CSV file. PL: Wtyczka geokodująca polskie adresy z pliku CSV

###### Sample geocoding input file/  Przykładowy plik do geokodowania:
```
miasto,ulica,kod,numer
Warszawa, Szeligowska, 01-320, 32A
Marki, Andersa,, 1
Słupno, Lipowa, 09-472, 4
Słupno, Lipowa, 05-250, 4
```
