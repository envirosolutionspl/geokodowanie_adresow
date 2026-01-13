# -*- coding: utf-8 -*-

import unittest
import os
import sys
from unittest.mock import MagicMock

current_dir = os.path.dirname(os.path.abspath(__file__))
plugin_dir = os.path.dirname(current_dir)
plugins_dir = os.path.dirname(plugin_dir)
sys.path.insert(0, plugins_dir)

from geokodowanie_adresow.geokodowanie_adresow import GeokodowanieAdresow
from qgis.core import (
    QgsApplication,
    QgsNetworkAccessManager,
    QgsNetworkReplyContent
)
from qgis.PyQt.QtCore import QUrl, QEventLoop
from qgis.PyQt.QtNetwork import QNetworkRequest, QNetworkReply
from unittest.mock import MagicMock, patch
from constants import CSV_URL

if not hasattr(QEventLoop, 'exec'):
    QEventLoop.exec = QEventLoop.exec_

# --- MOCKI POMOCNICZE ---
class MockMessageBar:
    def pushMessage(self, title, text, level=None, duration=None):
        # logowanie błędów
        print(f"[QGIS MessageBar] {title}: {text}")

class MockIface:
    def mainWindow(self):
        return MagicMock()
    def addToolBar(self, name):
        return MagicMock()
    def messageBar(self):
        return MockMessageBar()

class TestGeokodowanieIntegrated(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Inicjalizacja QGIS"""
        cls.qgs = QgsApplication([], False)
        cls.qgs.initQgis()
        
    @classmethod
    def tearDownClass(cls):
        cls.qgs.exitQgis()

    def setUp(self):
        self.mock_iface = MockIface()
        self.temp_csv_path = os.path.join(
            current_dir, 'temp_downloaded_data.csv'
        )
        self.temp_output_path = os.path.join(
            current_dir, 'temp_output.txt'
        )
        
        patch_path_settings = 'geokodowanie_adresow.geokodowanie_adresow.QSettings'
        
        # QgisFeed jest importowane wewnątrz __init__ z pliku qgis_feed.py.
        # Musimy zpatchować oryginał w module 'qgis_feed', 
        # aby import wewnątrz __init__ pobrał Mocka.
        patch_path_feed = 'geokodowanie_adresow.qgis_feed.QgisFeed'
        
        with patch(patch_path_settings) as MockQSettings, \
             patch(patch_path_feed) as MockFeed:
            # Konfigurujemy QSettings
            mock_settings_instance = MockQSettings.return_value
            mock_settings_instance.value.return_value = 'pl_PL'
            
            # Tworzymy instancję wtyczki
            self.plugin = GeokodowanieAdresow(self.mock_iface)

        self.plugin.taskManager = MagicMock()
        self.plugin.dlg = MagicMock()

    def tearDown(self):
        if os.path.exists(self.temp_csv_path):
            try:
                os.remove(self.temp_csv_path)
            except PermissionError:
                pass
        if os.path.exists(self.temp_output_path):
            try:
                os.remove(self.temp_output_path)
            except PermissionError:
                pass

    def downloadCsv(self):
        """
        Pobieranie pliku przez QgsNetworkAccessManager 
        (zgodnie z uwagami recenzenta)
        """
        manager = QgsNetworkAccessManager.instance()
        request = QNetworkRequest(QUrl(CSV_URL))
        
        loop = QEventLoop()
        reply = manager.get(request)
        reply.finished.connect(loop.quit)
        loop.exec()
        error_val = reply.error()
        
        if hasattr(QNetworkReply, 'NetworkError'):
            no_err = QNetworkReply.NetworkError.NoError # Qt6
        else:
            no_err = QNetworkReply.NoError # Qt5
        
        if error_val != no_err:
            self.fail(f"Błąd pobierania pliku: {reply.errorString()}")

        content = reply.readAll()
        with open(self.temp_csv_path, 'wb') as f:
            f.write(content)
        
        reply.deleteLater()
        return True

    def testParseCsvAndGeocodeFlow(self):
        """
        Testuje przepływ: Pobranie -> parseCsv -> Uruchomienie workera
        """
        self.downloadCsv()
        
        # Konfigurowanie wtyczki
        #self.plugin.inputPlik = self.temp_csv_path
        #self.plugin.outputPlik = os.path.join(
        #    os.path.dirname(__file__), 'temp_output.txt'
        #)
        self.plugin.delimeter = ','

        self.plugin.dlg.qfwInputFile.filePath.return_value = self.temp_csv_path
        self.plugin.dlg.qfwOutputFile.filePath.return_value = self.temp_output_path
        
        # Konfigurujemy odpowiedzi Mocka na pytania o wybrane indeksy 
        # w ComboBoxach.
        # Zakładamy strukturę pliku CSV: Miejscowość, Ulica, Kod, Numer
        # Przyjmijmy, że w CSV kolumny to: 0:Miasto, 1:Ulica, 2:Numer, 3:Kod
        
        self.plugin.dlg.cbxMiejscowosc.currentIndex.return_value = 1  
        self.plugin.dlg.cbxUlica.currentIndex.return_value = 2        
        self.plugin.dlg.cbxNumer.currentIndex.return_value = 4        
        self.plugin.dlg.cbxKod.currentIndex.return_value = 3          
        
        self.plugin.dlg.cbxEncoding.currentText.return_value = 'utf-8'
        self.plugin.dlg.cbxFirstRow.isChecked.return_value = True

        # URUCHOMIENIE LOGIKI WTYCZKI
        result = self.plugin.parseCsv()
        
        if result is False:
            self.fail(
                "Metoda parseCsv zakończyła się błędem (zwróciła False). "
                "Sprawdź logi MessageBar."
            )

        # WERYFIKACJA CZY ZADANIE ZOSTAŁO UTWORZONE
        self.plugin.taskManager.addTask.assert_called_once()
        
        # Wyciągamy obiekt zadania (Geokodowanie), z addTask
        created_task = self.plugin.taskManager.addTask.call_args[0][0]
        
        self.assertIsNotNone(
            created_task, "Zadanie Geokodowania nie zostało utworzone."
        )
        
        print(
            "Liczba wierszy przekazanych do zadania: "
            f"{len(created_task.rekordy)}"
        )
        self.assertGreater(
            len(created_task.rekordy), 0, "Lista rekordów jest pusta!"
        )
        
        self.assertEqual(
            len(created_task.miejscowosci), len(created_task.rekordy)
        )
        
        # URUCHOMIENIE SAMEGO ZADANIA
        worker_result = created_task.run()
        
        self.assertTrue(worker_result, "Worker zwrócił False")
        
        total_found = len(created_task.featuresPoint) + \
                      len(created_task.featuresLine) + \
                      len(created_task.featuresPoly)
                      
        print(
            f"Zgeokodowano: {total_found}/{len(created_task.rekordy)} obiektów."
        )
        self.assertGreater(
            total_found, 0, 
            "Geokoder nie zwrócił żadnych wyników!"
        )
        
        if created_task.bledne:
            print("Błędne adresy:", created_task.bledne)
        self.assertEqual(
            len(created_task.bledne), 0, "Znaleziono błędne adresy."
        )

if __name__ == "__main__":
    unittest.main()