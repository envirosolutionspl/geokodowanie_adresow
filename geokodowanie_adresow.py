# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Geokodowanie adresów UUG GUGiK
                                 A QGIS plugin
 Wtyczka geokoduje adresy z pliku do warstwy punktowej
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2024-12-13
        git sha              : $Format:%H$
        copyright            : (C) 2024 by EnviroSolutions Sp. z o.o.
        email                : office@envirosolutions.pl
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon, QPixmap
from qgis.PyQt.QtWidgets import QAction, QToolBar
from qgis.core import Qgis, QgsApplication, QgsVectorLayer, QgsProject, QgsWkbTypes
from qgis.PyQt.QtWidgets import QAction, QToolBar, QShortcut, QWidget, QLabel, QDialog, QComboBox
from PyQt5 import uic
from PyQt5.QtWidgets import QFileDialog
from qgis.core import QgsSettings
from . import encoding
from os import path
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import re
import requests


# Initialize Qt resources from file resources.pys
from .resources import *
# Import the code for the dialog
from .geokodowanie_adresow_dialog import GeokodowanieAdresowDialog
from .qgis_feed import QgisFeedDialog
from .geokoder import Geokodowanie

"""Wersja wtyczki"""
plugin_version = '1.2.4'
plugin_name = 'Geokodowanie adresów UUG GUGiK'


class GeokodowanieAdresow:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """

        self.settings = QgsSettings() 

        if Qgis.QGIS_VERSION_INT >= 31000:
            from .qgis_feed import QgisFeed
            self.selected_industry = self.settings.value("selected_industry", None)
            show_dialog = self.settings.value("showDialog", True, type=bool)

            if self.selected_industry is None and show_dialog:
                self.showBranchSelectionDialog()

            select_indust_session = self.settings.value('selected_industry')

            self.feed = QgisFeed(selected_industry=select_indust_session, plugin_name=plugin_name)
            self.feed.initFeed()

        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = path.join(
            self.plugin_dir,
            'i18n',
            'GeokodowanieAdresow_{}.qm'.format(locale))

        if path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        # self.geokodowanie = Geokodowanie(self.iface)
        self.menu = self.tr(u'&EnviroSolutions')

        # toolbar
        self.toolbar = self.iface.mainWindow().findChild(QToolBar, 'EnviroSolutions')
        if not self.toolbar:
            self.toolbar = self.iface.addToolBar(u'EnviroSolutions')
            self.toolbar.setObjectName(u'EnviroSolutions')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None
        self.taskManager = QgsApplication.taskManager()
        self.project = QgsProject.instance()

        
    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('GeokodowanieAdresow', message)

      
    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None
        ):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            # self.iface.addToolBarIcon(action)
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

      
    def initGui(self):
        self.dlg = GeokodowanieAdresowDialog()
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        self.dlg.qfwOutputFile.setFilter(filter="Pliki tekstowe (*.txt)")
        self.dlg.qfwInputFile.setFilter(filter="Pliki CSV (*.csv)")
        icon_path = ':/plugins/geokodowanie_adresow/images/icon_uug.svg'
        self.add_action(
            icon_path,
            text=self.tr(plugin_name),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True

        
    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&EnviroSolutions'),
                action)
            # self.iface.removeToolBarIcon(action)
            self.toolbar.removeAction(action)

            
    def run(self):
        """Run method that performs all the real work"""
        
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        if self.first_start == True:
            self.first_start = False
            self.dlg.qfwInputFile.fileChanged.connect(self.openInputFile)
            self.dlg.qfwOutputFile.fileChanged.connect(self.saveOutputFile)
            self.dlg.btnGeokoduj.clicked.connect(self.parseCsv)
            self.dlg.cbxDelimiter.currentTextChanged.connect(self.led_symbol_changed)
            self.dlg.cbxDelimiter.activated.connect(self.readHeader)
            self.isInputFile = False
            self.isOutputFile = False

            self.dlg.cbxEncoding.addItems(encoding.encodings)
            utf8Id = self.dlg.cbxEncoding.findText('utf_8')
            self.dlg.cbxEncoding.setCurrentIndex(utf8Id)
            self.dlg.cbxEncoding.currentIndexChanged.connect(self.readHeader)

            self.led_symbol_changed()

            # Inicjacja grafik
            self.dlg.img_main.setPixmap(QPixmap(':/plugins/geokodowanie_adresow/images/icon_uug.svg'))

            # rozmiar okna
            # self.dlg.setFixedSize(self.dlg.size())

            # informacje o wersji
            self.dlg.setWindowTitle('%s %s' % (plugin_name, plugin_version))
            self.dlg.lbl_pluginVersion.setText('%s %s' % (plugin_name, plugin_version))

        #connection = self.check_internet_connection()
        #if not connection:
        #    self.iface.messageBar().pushMessage(
        #        "Błąd",
        #        "Brak połączenia z internetem",
        #        level=Qgis.Warning,
        #        duration=10
        #    )
        #    return
        #else:
            # show the dialog
        self.taskManager.cancelAll()
        self.dlg.show()
            # Run the dialog event loop
        result = self.dlg.exec_()
            # See if OK was pressed
        if result:
            pass

    def showBranchSelectionDialog(self):
        self.qgisfeed_dialog = QgisFeedDialog()

        if self.qgisfeed_dialog.exec_() == QDialog.Accepted:
            self.selected_branch = self.qgisfeed_dialog.comboBox.currentText()
            
            #Zapis w QGIS3.ini
            self.settings.setValue("selected_industry", self.selected_branch, QgsSettings.NoSection)  
            self.settings.setValue("showDialog", False, QgsSettings.NoSection) 
            self.settings.sync()
              
    def openInputFile(self):
        """
        Otwiera okno dialogowe do wyboru pliku CSV.
        Po wybraniu pliku aktualizuje interfejs użytkownika.
        """

        # Wywołuje okno dialogowe do wyboru pliku CSV i zapisuje ścieżkę do zmiennej self.plik
        self.inputPlik = self.dlg.qfwInputFile.filePath()
        
        # Sprawdza, czy użytkownik wybrał plik
        if self.inputPlik != '':
            # Ustawia flagę isInputFile na True, aby oznaczyć, że plik został wybrany
            self.isInputFile = True
            
            # Sprawdza, czy oba pliki wejściowy i wyjściowy są wybrane, jeśli tak, 
            # umożliwia użytkownikowi uruchomienie procesu geokodowania przez aktywowanie przycisku btnGeokoduj
            if self.isInputFile and self.isOutputFile:
                self.dlg.btnGeokoduj.setEnabled(True)
            
            # Wywołuje funkcję readHeader() w celu odczytania nagłówków pliku CSV
            self.readHeader()

            
    def saveOutputFile(self):
        """
        Otwiera okno dialogowe do zapisu pliku tekstowego.
        Po wybraniu miejsca zapisu aktualizuje interfejs użytkownika.
        """
        
        # Wywołuje okno dialogowe do zapisu pliku tekstowego i zapisuje ścieżkę do zmiennej self.outputPlik
        self.outputPlik = self.dlg.qfwOutputFile.filePath()
        
        # Sprawdza, czy użytkownik wybrał miejsce zapisu pliku
        if self.outputPlik != '':
            # Ustawia flagę isOutputFile na True, aby oznaczyć, że miejsce zapisu pliku zostało wybrane
            self.isOutputFile = True
            
            # Sprawdza, czy oba pliki wejściowy i wyjściowy są wybrane, jeśli tak, 
            # umożliwia użytkownikowi uruchomienie procesu geokodowania przez aktywowanie przycisku btnGeokoduj
            if self.isInputFile and self.isOutputFile:
                self.dlg.btnGeokoduj.setEnabled(True)

                
    def readHeader(self):
        """
        Czyści ComboBoxy w interfejsie użytkownika.

        Sprawdza, czy plik wejściowy został wybrany. 
        Jeśli tak, otwiera plik i odczytuje pierwszą linię (nagłówek).
        Jeśli wystąpi błąd UnicodeDecodeError podczas odczytu pliku, wyświetla komunikat ostrzegawczy i przerywa działanie funkcji.
        W przeciwnym razie odczytuje elementy nagłówka, rozdzielając je na listę elementów za pomocą określonego separatora (delimeter).
        Następnie dodaje elementy nagłówka do odpowiednich ComboBoxów w interfejsie użytkownika.
        """
        
        # Czyści ComboBoxy w interfejsie użytkownika
        self.dlg.cbxMiejscowosc.clear()
        self.dlg.cbxUlica.clear()
        self.dlg.cbxNumer.clear()
        self.dlg.cbxKod.clear()

        # Sprawdza, czy plik wejściowy został wybrany
        if self.isInputFile:
            # Otwiera plik z wybraną ścieżką, odczytuje pierwszą linię (nagłówek) i przypisuje do zmiennej naglowki
            with open(self.inputPlik, 'r', encoding=self.dlg.cbxEncoding.currentText()) as plik:
                try:
                    naglowki = plik.readline()
                except UnicodeDecodeError:
                    # Wyświetla komunikat o błędzie kodowania, jeśli wystąpi błąd podczas odczytu pliku
                    self.iface.messageBar().pushMessage(
                        "Błąd kodowania:",
                        "Nie udało się zastosować wybranego kodowania do pliku z adresami. Spróbuj innego kodowania.",
                        level=Qgis.Warning, 
                        duration=5
                    )
                    # Przerywa działanie funkcji
                    return False
                
                # Rozdziela elementy nagłówka za pomocą określonego separatora i usuwa białe znaki z każdego elementu
                elementyNaglowkow = naglowki.split(self.delimeter)
                elementyNaglowkow = [x.strip() for x in elementyNaglowkow]  
                elementyNaglowkow.insert(0, "")  # Wstawia pusty element na początek listy
                
                # Dodaje elementy nagłówka do odpowiednich ComboBoxów w interfejsie użytkownika
                self.dlg.cbxMiejscowosc.addItems(elementyNaglowkow)
                self.dlg.cbxUlica.addItems(elementyNaglowkow)
                self.dlg.cbxNumer.addItems(elementyNaglowkow)
                self.dlg.cbxKod.addItems(elementyNaglowkow)

                
    def csvCheck(
            self, 
            rekordy, 
            idMiejscowosc, 
            idUlica, 
            idNumer, 
            idKod
        ):
        """Sprawdzenie poprawności CSV"""
        
        for rekord in rekordy:  # rekord:
            wartosci = rekord.strip().split(self.delimeter)  # lista wartosci w ramach jednego rekordu          
            try:
                if idMiejscowosc:
                    wartosci[idMiejscowosc - 1]
                if idUlica:
                    wartosci[idUlica - 1]
                if idNumer:
                    wartosci[idNumer - 1]
                if idKod:
                    wartosci[idKod - 1]

            except IndexError:
                self.iface.messageBar().pushMessage(
                    "Błąd wczytywania pliku:",
                    "błąd w wierszu nr %d: %s" % (rekordy.index(rekord), rekord),
                    level=Qgis.Critical, 
                    duration=5
                )
                return False  # wystąpiły błędy
        return True  # poprawnie wczytano wszystkie wiersze

      
    def createEmptyLayer(
            self, 
            headings, 
            hasHeadings=True
        ):
        """
        Tworzy pustą warstwę wektorową.

        Tworzy ciąg pól warstwy na podstawie nagłówków lub indeksów.
        Tworzy obiekt warstwy wektorowej punktów w pamięci.
        Zwraca obiekt warstwy wektorowej.

        :param headings: Lista nagłówków lub indeksów pól.
        :param hasHeadings: Określa, czy nagłówki są dostępne (domyślnie True).
        :return: Obiekt warstwy wektorowej.
        """
        
        # Ciąg pól warstwy na podstawie nagłówków lub indeksów
        fields = ''
        if hasHeadings:
            for heading in headings:
                fields += "&field=%s:string(0,-1)" % heading
        else:
            for i in range(len(headings)):
                fields += "&field=pole%i:string(0,-1)" % (i + 1)

        warstwaPoint = QgsVectorLayer(
            "Point?crs=EPSG:2180" + fields
            , "zgeokodowane lokalizacje", "memory")
        warstwaLine = QgsVectorLayer(
            "LineString?crs=EPSG:2180" + fields
            , "zgeokodowane ulice", "memory")
        warstwaPoly = QgsVectorLayer(
            "Polygon?crs=EPSG:2180" + fields
            , "zgeokodowane place", "memory")
        
        return warstwaPoint, warstwaLine, warstwaPoly


    def parseCsv(self):
        """
        Parsuje plik CSV, przetwarza jego zawartość i inicjuje proces geokodowania.

        Sprawdza, czy wybrane atrybuty są poprawnie wybrane, czy plik CSV jest poprawny, a następnie
        przetwarza rekordy, tworzy listy wartości dla poszczególnych atrybutów i inicjuje proces geokodowania.

        """
        
        """connection = self.check_internet_connection()
        if not connection:
            self.iface.messageBar().pushMessage(
                "Błąd",
                "Brak połączenia z internetem",
                level=Qgis.Warning,
                duration=10
            )
            return"""
        # Pobiera indeksy wybranych atrybutów
        idMiejscowosc = self.dlg.cbxMiejscowosc.currentIndex()
        idUlica = self.dlg.cbxUlica.currentIndex()
        idNumer = self.dlg.cbxNumer.currentIndex()
        idKod = self.dlg.cbxKod.currentIndex()

        # Sprawdza, czy co najmniej jeden atrybut jest wybrany
        if not idMiejscowosc and not idUlica and not idNumer and not idKod:
            # Informuje użytkownika, że nie wybrano żadnych atrybutów
            self.iface.messageBar().pushMessage(
                "Informacja: ", 
                "Nie wybrano żadnych atrybutów.", 
                Qgis.Info, 
                duration =10
            )
        # Sprawdza, czy wybrano miejscowość, jeśli nie, informuje użytkownika
        elif not idMiejscowosc:
            self.iface.messageBar().pushMessage(
                "Informacja: ", 
                "Nie wybrano miejscowości.", 
                Qgis.Info, 
                duration =10
            )
        else:
            # Inicjalizuje listy dla poszczególnych atrybutów
            miejscowosci = []
            ulicy = []
            numery = []
            kody = []

            # Otwiera plik CSV i przetwarza jego zawartość
            with open(self.inputPlik, 'r', encoding=self.dlg.cbxEncoding.currentText()) as plik:
                
                try:
                    zawartosc = plik.readlines()  # całość jako lista tekstowych linijek
                except UnicodeDecodeError:
                    return False

                # Pobiera nagłówek i dzieli go na listę wartości
                self.naglowek = zawartosc[0]
                naglowki = self.naglowek.strip().split(self.delimeter)  # lista wartosci w ramach naglowka

                # Sprawdza, czy pierwszy wiersz to nagłówek
                if self.dlg.cbxFirstRow.isChecked():
                    self.rekordy = zawartosc[1:]
                    self.warstwaPoint, self.warstwaLine, self.warstwaPoly= self.createEmptyLayer(
                        headings=naglowki, 
                        hasHeadings=True
                    )
                else:
                    self.rekordy = zawartosc[:]
                    self.rekordy[0] = self.rekordy[0][1:]  # usuniecie pierwszego bitu zwiazanego z poczatkiem pliku
                    self.warstwaPoint, self.warstwaLine, self.warstwaPoly = self.createEmptyLayer(
                        headings=naglowki, 
                        hasHeadings=False
                    )

                # sprawdzenie czy plik CSV jest poprawny
                if not self.csvCheck(self.rekordy, idMiejscowosc, idUlica, idNumer, idKod):
                    return False
                
                # Przetwarza rekordy i tworzy listy wartości dla poszczególnych atrybutów
                for rekord in self.rekordy:
                    
                    try:
                        wartosci = rekord.strip().split(self.delimeter)
                        miejscowosci.append(wartosci[idMiejscowosc - 1] if idMiejscowosc else "")
                        ulicy.append(self.dealWithAbbreviations(wartosci[idUlica - 1]) if idUlica else "")
                        numery.append(self.korektaFormatu(wartosci[idNumer - 1].upper()) if idNumer else "")
                        kody.append(self.korektaFormatu(wartosci[idKod - 1]) if idKod else "")

                    except Exception as e:
                        # Informuje o błędzie podczas przetwarzania rekordu
                        self.iface.messageBar().pushMessage(
                            "Błąd przetwarzania rekordu", 
                            str(e), 
                            level=Qgis.Critical, 
                            duration=3
                        )
                        continue

                # Tworzy obiekt zadania geokodowania i dodaje je do menedżera zadań
                task = Geokodowanie(
                    rekordy = self.rekordy, 
                    miejscowosci = miejscowosci, 
                    ulicy = ulicy, 
                    numery = numery, 
                    kody = kody,
                    delimeter = self.delimeter, 
                    iface = self.iface,
                )

                self.taskManager.addTask(task)
                self.dlg.btnGeokoduj.setEnabled(False)  
                
            task.finishedProcessing.connect(self.geokodowanieSukces)
    

    def korektaFormatu(self, numer):
        """
        Korektuje format numeru.

        Sprawdza, czy numer zawiera cudzysłów.
        Jeśli tak, usuwa go.
        Zwraca skorygowany numer.
        """
        
        # Sprawdza, czy cudzysłów występuje w numerze
        if '"' in numer:
            # Usuwa cudzysłów
            numer = numer.replace('"', '')
        return numer

      
    def dealWithAbbreviations(self, text):
        """
        Przetwarza skróty na pełne nazwy.

        Tworzy słownik przekształceń skrótów na pełne nazwy.
        Tworzy wyrażenie regularne z przekształconych skrótów.
        Zamienia skróty na pełne nazwy w tekście.
        Zamienia polskie cudzysłowy na standardowe cudzysłowy.
        Zwraca przekształcony tekst.
        """
        
        # Słownik przekształceń skrótów na pełne nazwy
        rep = {"al.": "aleje", "Al.": "Aleje", "Pl.": "Plac", "pl.": "plac", "ul.":"", "Ul.":""}
        # Tworzy słownik przekształceń ze znakami ucieczki dla wyrażeń regularnych

        rep = dict((re.escape(k), v) for k, v in rep.items())
        # Tworzy wyrażenie regularne z przekształconych skrótów
        self.pattern = re.compile("|".join(rep.keys()))
        # Zamienia skróty na pełne nazwy w tekście
        text = self.pattern.sub(lambda m: rep[re.escape(m.group(0))], text)
        # Zamienia polskie cudzysłowy na standardowe cudzysłowy
        if "„" in text or "”" in text:
            text = text.replace("„", '"').replace("”", '"')
        # Zwraca przekształcony tekst
        return text    

      
    def led_symbol_changed(self):
        """
        Obsługuje zmianę symbolu separacji.

        Aktualizuje zmienną self.delimeter na podstawie wybranej opcji
        z listy rozwijanej w interfejsie użytkownika.
        """
        
        # Aktualizuje self.delimeter na podstawie aktualnie wybranej opcji
        self.delimeter = self.dlg.cbxDelimiter.currentText()

        # Jeśli symbol separacji jest pusty, ustawia domyślny przecinek
        if self.delimeter == '':
            self.delimeter = ','

        # Jeśli symbol separacji to "Spacja", ustawia spację
        if self.delimeter == "Spacja":
            self.delimeter = ' '

            
    def saveErrors(self, listaWierszy):
        """
        Zapisuje błędne adresy do pliku tekstowego.
        """
        
        # Otwiera plik wyjściowy w trybie zapisu
        with open(self.outputPlik, 'w') as plik: 
            # Zapisuje wszystkie wiersze z listy do pliku
            plik.writelines(listaWierszy)


    def geokodowanieSukces(
                self, 
                featuresPoint, 
                featuresLine, 
                featuresPoly, 
                bledne, 
                stop
        ):
        """
        Funkcja przetwarza wyniki geokodowania, dodając je do odpowiednich warstw w QGIS,
        aktualizując te warstwy oraz wyświetlając odpowiednie komunikaty.

        Parametry:
            featuresPoint (list): Lista obiektów geometrii punktowej.
            featuresLine (list): Lista obiektów geometrii liniowej.
            featuresPoly (list): Lista obiektów geometrii poligonowej.
            bledne (list): Lista błędnych adresów, które nie zostały zgeokodowane.
            stop (bool): Flaga wskazująca, czy proces geokodowania został zatrzymany.
        """
        
        # Zgrupowanie warstw do jednej listy
        warstwy = [self.warstwaPoint, self.warstwaLine, self.warstwaPoly]
        
        # Włączenie przycisku "Geokoduj"
        self.dlg.btnGeokoduj.setEnabled(True)
        
        # Dodanie obiektów do odpowiednich warstw danych
        self.warstwaPoint.dataProvider().addFeatures(featuresPoint)
        self.warstwaLine.dataProvider().addFeatures(featuresLine)
        self.warstwaPoly.dataProvider().addFeatures(featuresPoly)
        
        # Aktualizacja zakresu i dodanie warstw do projektu
        for warstwa in warstwy:
            warstwa.updateExtents()
            if warstwa.featureCount() > 0:
                self.project.addMapLayer(warstwa)
        
        # Obliczenie liczby zgeokodowanych rekordów i całkowitej liczby rekordów
        iloscZgeokodowanych = len(featuresLine) + len(featuresPoint) + len(featuresPoly)
        iloscRekordow = len(self.rekordy)
        
        # Wyświetlenie komunikatu, jeśli proces geokodowania został zatrzymany
        if stop:
            self.iface.messageBar().pushMessage(
                "Proces geokodowania został zatrzymany:",
                "Zgeokodowano %i/%i adresów. Błędnie zgeokodowane adresy zostały zapisane w pliku %s" % (
                    iloscZgeokodowanych,
                    iloscRekordow,
                    self.outputPlik
                ), 
                level=Qgis.Info,
                duration=5
            )
        
        # Wyświetlenie komunikatu, jeśli są błędne adresy lub żaden adres nie został zgeokodowany
        elif bledne or iloscZgeokodowanych == 0:
            iloscBledow = len(bledne)
            bledne.insert(0, "Miejscowość,Ulica,Numer Porządkowy,Kod Pocztowy \n")
            self.saveErrors(bledne)
            
            self.iface.messageBar().pushMessage(
                "Wynik geokodowania:",
                "Zgeokodowano %i/%i adresów. Pozostałe zostały zapisane w pliku %s" % (
                    iloscZgeokodowanych,
                    iloscRekordow,
                    self.outputPlik
                ), 
                level=Qgis.Info,
                duration=5
            )
        
        # Wyświetlenie komunikatu, jeśli liczba zgeokodowanych adresów jest większa niż liczba rekordów
        elif iloscZgeokodowanych > iloscRekordow:
            self.iface.messageBar().pushMessage(
                "Wynik geokodowania:",
                "Zgeokodowano %i/%i adresów. Dla niektórych adresów usługa geokodowania zwróciła kilka wartości." % (
                    iloscZgeokodowanych,
                    iloscRekordow
                ),
                level=Qgis.Success,
                duration=5
            )
        
        # Wyświetlenie komunikatu, jeśli wszystkie adresy zostały poprawnie zgeokodowane
        elif not bledne:
            self.iface.messageBar().pushMessage(
                "Wynik geokodowania:",
                "Zgeokodowano wszystkie %i adresów" % (
                    iloscZgeokodowanych
                ),
                level=Qgis.Success,
                duration=5
            )
            
            
    def check_internet_connection(self):
        try:
            session = requests.Session()
            with session.get(url='https://www.envirosolutions.pl', verify=False) as resp:
                if resp.status_code != 200:
                    return False
                return True
        except requests.exceptions.ConnectionError:
            return False
        finally:
            session.close()
