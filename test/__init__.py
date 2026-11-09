import os
import sys

_PLUGIN_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PLUGINS_DIR = os.path.dirname(_PLUGIN_DIR)

if _PLUGINS_DIR not in sys.path:
    sys.path.insert(0, _PLUGINS_DIR)
