# -*- coding: utf-8 -*-

import unittest
import os
import sys
import csv
from qgis.core import (
    QgsApplication,
    QgsProject,
    QgsGeometry
)

# Dodanie ścieżki do głównego katalogu wtyczki
PLUGIN_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(PLUGIN_DIR)

# Import klas wtyczki
from geokoder import Geokodowanie

# --- MOCKOWANIE INTERFEJSU QGIS ---
class MockMessageBar:
    def pushMessage(self, title, text, level=None, duration=None):
        print(f"[QGIS MessageBar] {title}: {text}")

class MockIface:
    def messageBar(self):
        return MockMessageBar()

# ----------------------------------

class TestGeokodowanieLocal(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Inicjalizacja QGIS (tryb headless - bez GUI)"""
        cls.qgs = QgsApplication([], False)
        cls.qgs.initQgis()
        
    @classmethod
    def tearDownClass(cls):
        """Zamknięcie QGIS"""
        cls.qgs.exitQgis()

    def setUp(self):
        """Przygotowanie: Tworzenie pliku CSV z danymi testowymi"""
        self.mock_iface = MockIface()
        self.temp_csv_path = os.path.join(os.path.dirname(__file__), 'temp_test_data.csv')
        
        # Twoje dane testowe
        # Format: Miasto, Ulica, Kod, Numer
        self.header = ["Miasto", "Ulica", "Kod", "Numer"]
        self.data_rows = [
            ["Warszawa", "Agrykola", "00-467", "1"],
            ["Warszawa", "Plac Defilad", "", "1"],       # Brak kodu
            ["Kraków", "Wawel", "31-001", "5"],
            ["Słupno", "Lipowa", "09-472", "4"],
            ["Słupno", "Lipowa", "05-250", "4"],         # To samo miasto i ulica, inny kod (ważny test!)
            ["Warszawa", "Szeligowska", "01-320", "32A"] # Numer z literą
        ]
        
        # Zapisujemy plik CSV
        with open(self.temp_csv_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(self.header)
            writer.writerows(self.data_rows)
            
    def tearDown(self):
        """Sprzątanie: Usuwanie pliku CSV po teście"""
        if os.path.exists(self.temp_csv_path):
            try:
                os.remove(self.temp_csv_path)
            except PermissionError:
                pass

    def test_geokodowanie_poprawnosc_adresow(self):
        """
        Test sprawdza czy 6 konkretnych adresów z pliku CSV zostanie poprawnie zgeokodowanych.
        """
        print(f"Rozpoczynam test na pliku lokalnym: {self.temp_csv_path}")

        # 1. Symulacja wczytywania danych (logika z wtyczki)
        delimiter = ','
        
        # Indeksy kolumn w Twoim pliku (liczone od 0):
        # Miasto(0), Ulica(1), Kod(2), Numer(3)
        idx_miasto = 0
        idx_ulica = 1
        idx_kod = 2
        idx_numer = 3

        miejscowosci = []
        ulice = []
        numery = []
        kody = []
        rekordy_text = [] # Wtyczka przechowuje też surowe linie tekstu

        # Czytamy plik tak, jak robiłaby to wtyczka (jako tekst, żeby potem splitować)
        with open(self.temp_csv_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # Pomijamy nagłówek (zakładamy, że opcja cbxFirstRow jest zaznaczona)
        rekordy_text = lines[1:]
        
        print(f"Wczytano {len(rekordy_text)} adresów do sprawdzenia.")

        for i, line in enumerate(rekordy_text):
            # Symulacja prostego splitowania używanego we wtyczce
            # Uwaga: wtyczka używa .split(delimeter), co jest proste, ale działa dla Twoich danych
            parts = line.strip().split(delimiter)
            
            # Zabezpieczenie na wypadek pustych linii
            if not line.strip(): 
                continue

            # Pobieranie danych (zabezpieczone przed index error)
            # Używamy .strip(), żeby pozbyć się spacji np. po przecinku
            miasto = parts[idx_miasto].strip() if len(parts) > idx_miasto else ""
            ulica = parts[idx_ulica].strip() if len(parts) > idx_ulica else ""
            kod = parts[idx_kod].strip() if len(parts) > idx_kod else ""
            numer = parts[idx_numer].strip() if len(parts) > idx_numer else ""

            miejscowosci.append(miasto)
            ulice.append(ulica)
            kody.append(kod)
            numery.append(numer)
            
            print(f" -> Adres {i+1}: {miasto}, {ulica} {numer} (Kod: {kod})")

        # 2. Uruchomienie Geokodera
        print("Uruchamianie procesu geokodowania (może chwilę potrwać)...")
        
        task = Geokodowanie(
            rekordy=rekordy_text,
            miejscowosci=miejscowosci,
            ulicy=ulice,
            numery=numery,
            kody=kody,
            delimeter=delimiter,
            iface=self.mock_iface
        )

        # Uruchomienie synchroniczne
        result = task.run()
        
        # 3. Weryfikacja wyników
        self.assertTrue(result, "Metoda run() zwróciła False.")
        
        total_found = len(task.featuresPoint) + len(task.featuresLine) + len(task.featuresPoly)
        total_errors = len(task.bledne)
        
        print(f"Podsumowanie: Znaleziono {total_found}, Błędy {total_errors}")
        
        # Asercja 1: Powinniśmy znaleźć wszystkie 6 adresów
        # (Chyba że któryś jest nieistniejący w bazie GUGiK, ale te wyglądają na poprawne)
        self.assertEqual(total_found, 6, f"Oczekiwano 6 wyników, znaleziono {total_found}. Błędne: {task.bledne}")
        self.assertEqual(total_errors, 0, "Nie powinno być błędów geokodowania.")

        # Asercja 2: Sprawdzenie poprawności geometrii dla pierwszego wyniku (Warszawa Agrykola)
        # Zakładamy, że kolejność wyników jest zachowana (geokoder przetwarza w pętli)
        # Uwaga: featuresPoint może nie zawierać wyników w tej samej kolejności co input, 
        # bo to zależy czy wynik trafił do Points, Lines czy Poly. 
        # Ale w tym prostym przypadku pewnie większość to punkty.
        
        if task.featuresPoint:
            feat = task.featuresPoint[0]
            # Sprawdzenie czy atrybuty się zgadzają z pierwszym adresem
            attrs = feat.attributes()
            # Sprawdź czy w atrybutach jest "Warszawa" (powinno być, bo wtyczka przepisuje atrybuty z CSV)
            # Atrybuty są listą stringów z CSV splitniętą delimiterem
            self.assertIn("Warszawa", [str(a).strip() for a in attrs], "Brak nazwy miasta w atrybutach pierwszego wyniku")
            
            # Sprawdzenie geometrii
            geom = feat.geometry()
            self.assertTrue(geom.isGeosValid(), "Niepoprawna geometria")
            
            # Sprawdzenie czy Słupno (dwa różne kody) zostało rozróżnione?
            # To trudniejsze do sprawdzenia w prostym teście bez analizy przestrzennej,
            # ale sam fakt znalezienia 6 wyników sugeruje sukces.

if __name__ == "__main__":
    unittest.main()