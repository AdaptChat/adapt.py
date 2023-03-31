__author__ = 'jay3332'
__version__ = '0.1.0-alpha'

from . import client, http, util
from .client import Client, once
from .polyfill import polyfill as _polyfill
from .server import AdaptServer

_polyfill()
del _polyfill
