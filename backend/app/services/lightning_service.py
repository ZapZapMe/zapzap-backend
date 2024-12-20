from config import settings
from fastapi import HTTPException, status
import logging
import breez_sdk
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class SDKListener(breez_sdk.EventListener):
    def on_event(self, event):
        logging.info(event)

class SDKLogStream(breez_sdk.LogStream):
    def log(self, l):
        print("Received log [", l.level, "]: ", l.line)

def logging():
    try:
        breez_sdk.set_log_stream(SDKLogStream())
    except Exception as error:
        print(error)
        raise

def extract_payment_hash(ln_invoice: str):
    try:
        invoice = breez_sdk.decode_ln_invoice(ln_invoice)
        return invoice.payment_hash
    except Exception as error:

class LightningService:
    def __init__(self):
        self.api_key = settings.BREEZ_API_KEY
        self.base_url = settings.BREEZ_API_BASE_URL