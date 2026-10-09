"""
Flask konfigurációs modul.
"""
import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "bme-gtk-quant-calculator-secret-key-2026")
    JSON_SORT_KEYS = False
    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True

class ProductionConfig(Config):
    DEBUG = False
