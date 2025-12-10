# -*- coding: utf-8 -*-

import unittest
import os
import sys
import shutil
import urllib.request
import csv
from qgis.core import (
    QgsApplication,
    QgsProject,
    QgsGeometry
)
from constants import CSV_URL
from geokoder import Geokodowanie

# --- MOCKOWANIE INTERFEJSU QGIS ---
class MockMessageBar:
    def pushMessage(self, title, text, level=None, duration=None):
        print(f"[QGIS MessageBar] {title}: {text}")

class MockIface:
    def messageBar(self):
        return MockMessageBar()

class TestGeokodowanieOnline(unittest.TestCase):
    
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
        """Przygotowanie przed każdym testem"""
        self.mock_iface = MockIface()
        self.temp_csv_path = os.path.join(os.path.dirname(__file__), 
            'temp_downloaded_data.csv')

    def tearDown(self):
        """Sprzątanie po teście"""
        if os.path.exists(self.temp_csv_path):
            try:
                os.remove(self.temp_csv_path)
            except PermissionError:
                pass

    def downloadCsv(self):
        """Pobiera plik z internetu udając przeglądarkę"""
        try:
            req = urllib.request.Request(
                CSV_URL, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            
            with urllib.request.urlopen(req) as response, \
                    open(self.temp_csv_path, 'wb') as out_file:
                shutil.copyfileobj(response, out_file)

            return True
        except Exception as e:
            self.fail(f"Nie udało się pobrać pliku CSV. Błąd: {e}")

    def testGeokodowanieZPlikuOnline(self):
        """
        Główny test: Uruchamia geokoder.
        """
        
        self.downloadCsv()
        
        miejscowosci = []
        ulice = []
        numery = []
        kody = []
        rekordy_text = []
        
        with open(self.temp_csv_path, 'r', encoding='utf-8', newline='') \
                as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            all_rows = list(reader)

            if len(all_rows) < 2:
                self.fail("Pobrany plik CSV jest pusty lub zawiera tylko nagłówek!")

            headers = all_rows[0]
            if headers and headers[0].startswith('\ufeff'):
                headers[0] = headers[0].replace('\ufeff', '')

            if len(headers) == 1 and ',' in headers[0]:
                headers = [h.strip() for h in headers[0].split(',')]

            headers = [h.strip() for h in headers]

            try:
                headers_lower = [h.lower() for h in headers]
                idx_miasto = headers_lower.index('miasto')
                idx_ulica = headers_lower.index('ulica')
                idx_kod = headers_lower.index('kod')
                idx_numer = headers_lower.index('numer')
            except ValueError as e:
                self.fail(
                    "Nie znaleziono wymaganej kolumny w pliku CSV! "
                    f"Błąd: {e}. Dostępne kolumny: {headers}"
                    )

            data_rows = all_rows[1:]
            
            for row in data_rows:
                if not row or not any(row):
                    continue
                
                if len(row) == 1 and ',' in row[0]:
                     row = [r.strip() for r in row[0].split(',')]

                rekordy_text.append(",".join(row))
                miasto = row[idx_miasto].strip() if len(row) > idx_miasto else ""
                ulica = row[idx_ulica].strip() if len(row) > idx_ulica else ""
                kod = row[idx_kod].strip() if len(row) > idx_kod else ""
                numer = row[idx_numer].strip() if len(row) > idx_numer else ""
                miejscowosci.append(miasto)
                ulice.append(ulica)
                kody.append(kod)
                numery.append(numer)
        
        task = Geokodowanie(
            rekordy=rekordy_text,
            miejscowosci=miejscowosci,
            ulicy=ulice,
            numery=numery,
            kody=kody,
            delimeter=',',
            iface=self.mock_iface
        )

        result = task.run()
        self.assertTrue(result, "Metoda run() geokodera zwróciła False.")
        total_found = len(task.featuresPoint) + len(task.featuresLine) \
            + len(task.featuresPoly)
        total_errors = len(task.bledne)
        oczekiwana_liczba = len(miejscowosci)

        print(
            f"Wynik: Zgeokodowano {total_found}/{oczekiwana_liczba}."
            f" Błędnych: {total_errors}"
            )

        if total_errors > 0:
            print("Szczegóły błędów:")
            for err in task.bledne:
                print(f" [BŁĄD] {err.strip()}")

        self.assertEqual(total_errors, 0, "Znaleziono błędy geokodowania!")
        self.assertEqual(
            total_found, oczekiwana_liczba,
            "Liczba wyników niezgodna z liczbą wierszy"
            )

        if total_found > 0:
            feat_list = task.featuresPoint \
                if task.featuresPoint \
                else (task.featuresLine if task.featuresLine \
                else task.featuresPoly)
            feat = feat_list[0]
            self.assertTrue(
                feat.geometry().isGeosValid(),
                f"Niepoprawna geometria."
                )
            print("Wtyczka działa poprawnie.")

if __name__ == "__main__":
    unittest.main()