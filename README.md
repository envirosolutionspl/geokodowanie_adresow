# geokodowanie_uug
EN: QGIS 3 Plugin for geocoding addresses of Poland from CSV file. PL: Wtyczka geokodująca polskie adresy z pliku CSV

Wtyczka geokoduje polskie adresy na warstwę punktową w QGIS.
Obsługuje pliki tektowe CSV oddzielone przecinkami. Plik może (ale nie musi) zawierać nagłówki.

## changelog
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


###### Sample geocoding input file/  Przykładowy plik do geokodowania:
```
miasto,ulica,kod,numer
Warszawa, Szeligowska, 01-320, 32A
Marki, Andersa,, 1
Słupno, Lipowa, 09-472, 4
Słupno, Lipowa, 05-250, 4
```
