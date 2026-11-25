FEED_URL = 'https://qgisfeed.envirosolutions.pl/'
INDUSTRIES_URL = 'https://qgisfeed.enviro-dev.pl/industries/'
INDUSTRIES_TIMEOUT_MS = 3000

# Klucze QgsSettings wspólne dla wszystkich wtyczek EnviroSolutions w profilu QGIS
FEED_KEY_USER_ID = 'anonymous_user_id'
FEED_KEY_INDUSTRY = 'selected_industry'
FEED_APP_PROPERTY_DIALOG_HANDLED = 'envirosolutions_industry_dialog_handled'

REP = {
    "al.": "aleje", 
    "Al.": "Aleje", 
    "Pl.": "Plac", 
    "pl.": "plac", 
    "ul.": "", 
    "Ul.": ""
}

GUGIK = "https://services.gugik.gov.pl/uug/?"

PARAMS = {"request": "GetAddress"}

EPSG = 2180

CSV_URL = "https://downloads.envirosolutions.pl/sample-data.csv"

QT_VER = {
    6: "6."
}

HOME_LINK = "https://envirosolutions.pl/wtyczki-qgis/geokodowanie-adresow-uug-gugik/"

FOOTER_LINK_COLORS = {'light': '#556b55', 'dark': '#a9cfac'}

FOOTER_LOGOS = {'light': 'ESENG_poz_green.png', 'dark': 'ESENG_poz_white.png'}

THEME_ICONS = {
    'btn_help': 'help_primary.svg',
    'btnGeokoduj': 'pin_on_primary.svg'
}

DESCRIPTION_LABEL = "Adresy z pliku CSV na mapie - usługa UUG GUGiK ·"
