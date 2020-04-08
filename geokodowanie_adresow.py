# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Geokodowanie adresów UUG GUGiK
                                 A QGIS plugin
 Wtyczka geokoduje adresy z pliku do warstwy punktowej
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2019-12-13
        git sha              : $Format:%H$
        copyright            : (C) 2019 by Michał Włoga - EnviroSolutions Sp. z o.o.
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
from qgis.core import *
from PyQt5.QtWidgets import QFileDialog
from . import geokoder
from . import encoding

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .geokodowanie_adresow_dialog import GeokodowanieAdresowDialog
import os.path

"""Wersja wtyczki"""
plugin_version = '1.1.0'
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
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'GeokodowanieAdresow_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&EnviroSolutions')

        #toolbar
        self.toolbar = self.iface.mainWindow().findChild(QToolBar, 'EnviroSolutions')
        if not self.toolbar:
            self.toolbar = self.iface.addToolBar(u'EnviroSolutions')
            self.toolbar.setObjectName(u'EnviroSolutions')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

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
        parent=None):
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
            #self.iface.addToolBarIcon(action)
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/geokodowanie_adresow/images/icon.png'
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

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = GeokodowanieAdresowDialog()
            self.dlg.btnInputFile.clicked.connect(self.openInputFile)
            self.dlg.btnOutputFile.clicked.connect(self.saveOutputFile)
            self.dlg.btnGeokoduj.clicked.connect(self.parseCsv)
            self.dlg.led_symbol.textChanged.connect(self.led_symbol_changed)
            self.dlg.led_symbol.editingFinished.connect(self.readHeader)
            self.isInputFile = False
            self.isOutputFile = False

            self.dlg.cbxEncoding.addItems(encoding.encodings)
            utf8Id = self.dlg.cbxEncoding.findText('utf_8')
            print(utf8Id)
            self.dlg.cbxEncoding.setCurrentIndex(utf8Id)
            self.dlg.cbxEncoding.currentIndexChanged.connect(self.readHeader)

            self.led_symbol_changed()

            # Inicjacja grafik
            self.dlg.img_main.setPixmap(QPixmap(':/plugins/geokodowanie_adresow/images/icon_uug.png'))

            # rozmiar okna
            self.dlg.setFixedSize(self.dlg.size())

            # informacje o wersji
            self.dlg.setWindowTitle('%s %s' % (plugin_name, plugin_version))
            self.dlg.lbl_pluginVersion.setText('%s %s' % (plugin_name, plugin_version))

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            pass

    def openInputFile(self):
        self.plik = QFileDialog.getOpenFileName()[0]
        if self.plik != '':
            # print(self.plik, type(self.plik))
            self.dlg.lblInputFile.setText(self.plik)

            self.isInputFile = True
            if self.isInputFile and self.isOutputFile:
                self.dlg.btnGeokoduj.setEnabled(True)

            self.readHeader()


    def saveOutputFile(self):
        self.outputPlik = QFileDialog.getSaveFileName(filter="Pliki tekstowe (*.txt)")[0]
        if self.outputPlik != '':
            self.dlg.lblOutputFile.setText(self.outputPlik)

            self.isOutputFile = True
            if self.isInputFile and self.isOutputFile:
                self.dlg.btnGeokoduj.setEnabled(True)

    def readHeader(self):
        self.dlg.cbxMiejscowosc.clear()
        self.dlg.cbxUlica.clear()
        self.dlg.cbxNumer.clear()
        self.dlg.cbxKod.clear()
        if self.isInputFile:
            with open(self.plik, 'r', encoding=self.dlg.cbxEncoding.currentText()) as plik:
                try:
                    naglowki = plik.readline()
                except UnicodeDecodeError:
                    self.iface.messageBar().pushMessage("Błąd kodowania:","Nie udało się zastosować wybranego kodowania do pliku z adresami. Spróbuj inne kodowanie", level=Qgis.Warning)
                    return False
                elementyNaglowkow = naglowki.split(self.delimeter)
                elementyNaglowkow = [x.strip() for x in elementyNaglowkow] #usuwa biale znaki dla kazdego elementu listy
                elementyNaglowkow.insert(0,"")
                # wczytywanie listy nagłówków do ComboBoxów
                self.dlg.cbxMiejscowosc.addItems(elementyNaglowkow)
                self.dlg.cbxUlica.addItems(elementyNaglowkow)
                self.dlg.cbxNumer.addItems(elementyNaglowkow)
                self.dlg.cbxKod.addItems(elementyNaglowkow)

    def parseCsv(self):
        idMiejscowosc = self.dlg.cbxMiejscowosc.currentIndex()
        idUlica = self.dlg.cbxUlica.currentIndex()
        idNumer = self.dlg.cbxNumer.currentIndex()
        idKod = self.dlg.cbxKod.currentIndex()

        sciezka = self.plik
        with open(sciezka, 'r', encoding=self.dlg.cbxEncoding.currentText()) as plik:
            try:
                zawartosc = plik.readlines()  # całość jako lista tekstowych linijek
            except UnicodeDecodeError:
                return False

            naglowek = zawartosc[0]
            if self.dlg.cbxFirstRow.isChecked():
                rekordy = zawartosc[1:]
            else:
                rekordy = zawartosc[:]

            warstwa = QgsVectorLayer("Point?crs=EPSG:2180&field=miasto:string(50,-1)&field=kod:string(10,-1)&field=ulica:string(50,-1)&field=numer:string(10,-1)"
                                     ,"zgeokodowane","memory")


            features = []
            bledne = []
            for rekord in rekordy:  # rekord:
                wartosci = rekord.split(self.delimeter)  # lista wartosci w ramach jednego rekordu
                wartosci = [x.strip() for x in wartosci]
                miejcowosc, ulica, numer, kod = "", "", "", ""
                if idMiejscowosc:
                    miejcowosc = wartosci[idMiejscowosc - 1]
                if idUlica:
                    ulica = wartosci[idUlica - 1]
                if idNumer:
                    numer = wartosci[idNumer - 1]
                if idKod:
                    kod = wartosci[idKod - 1]

                wkt = geokoder.geocode(miasto=miejcowosc, ulica=ulica, numer=numer, kod=kod)
                if isinstance(wkt,tuple):
                    #błąd serwera
                    response = wkt[0]
                    self.iface.messageBar().pushMessage("Błąd. Odpowiedź serwera GUGiK:",
                                                        response,
                                                        level=Qgis.Critical, duration=20)
                    return False

                elif wkt is not None:
                    #twórz obiekt punktowy
                    geom = QgsGeometry().fromWkt(wkt)
                    feat = QgsFeature()
                    feat.setGeometry(geom)
                    feat.setAttributes([miejcowosc, kod, ulica, numer])
                    features.append(feat)
                else:
                    #dodaj do pliku z błędami
                    bledne.append(self.delimieter.join(wartosci)+"\n")

            warstwa.dataProvider().addFeatures(features)
            warstwa.updateExtents()
            QgsProject.instance().addMapLayer(warstwa)

            iloscZgeokodowanych = len(features)

            #zapisanie blednych adresow do pliku
            if bledne: #jezeli cokolwiek zapisalo sie do listy bledne
                iloscBledow = len(bledne)

                bledne.insert(0,naglowek)
                self.saveErrors(bledne)

                self.iface.messageBar().pushMessage("Wynik geokodowania:",
                                                    "Zgeokodowano %i/%i adresów. Pozostałe zostały zapisane w pliku %s" % (
                                                        iloscZgeokodowanych,iloscBledow + iloscZgeokodowanych,
                                                        self.outputPlik),level=Qgis.Warning)
            else:
                #wszytsko zgeokodowano
                self.iface.messageBar().pushMessage("Wynik geokodowania:",
                                                    "Zgeokodowano wszystkie %i adresów" % (
                                                    iloscZgeokodowanych), level=Qgis.Success)

    def saveErrors(self, listaWierszy):
        with open(self.outputPlik, 'w') as plik:
            plik.writelines(listaWierszy)


    def led_symbol_changed(self):
        self.delimeter = self.dlg.led_symbol.text().strip()
        if self.delimeter == '':
            self.delimeter = ','



