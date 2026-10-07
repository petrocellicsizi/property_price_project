import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(app_name="calc_flask"):
    """
    Központosított logger beállítása az alkalmazáshoz.
    Létrehoz egy 'logs' mappát, ahova a részletes logok kerülnek rotálva.
    A konzolra csak az INFO és annál fontosabb üzeneteket írja ki olvasható formában.
    """
    if not os.path.exists('logs'):
        os.makedirs('logs')

    logger = logging.getLogger(app_name)
    logger.setLevel(logging.DEBUG)

    # Megakadályozzuk a duplikált handlereket, ha többször importálják
    if not logger.handlers:
        # 1. Konzol Handler (INFO szint, rövid formátum)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(module)s | %(message)s', datefmt='%H:%M:%S')
        console_handler.setFormatter(console_formatter)

        # 2. File Handler (DEBUG szint, részletes formátum, max 5MB/fájl, 3 backup)
        file_handler = RotatingFileHandler('logs/app.log', maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(module)s:%(lineno)d | %(message)s')
        file_handler.setFormatter(file_formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger

# Globális logger példány, amit minden modul importálhat
logger = setup_logger()
