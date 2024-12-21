import logging, time
import breez_sdk
from breez_sdk_liquid import default_config, ConnectRequest, ReceivePaymentRequest,ListPaymentsRequest, PaymentState, LiquidNetwork
from config import settings
import breez_sdk_liquid
from db import SessionLocal
from models.tip import Tip
from sqlalchemy.orm import Session


# Optional: define a global variable for 'sdk_services'
sdk_services = None

def mark_invoice_as_paid_in_db(invoice_or_hash: str):
    with SessionLocal() as db:
        tip = db.query(Tip).filter(Tip.ln_payment_hash == invoice_or_hash).first()
        if not tip:
            tip = db.query(Tip).filter(Tip.bolt11_invoice == invoice_or_hash).first()
        
        if tip and not tip.paid:
            tip.paid = True
            db.commit()
            logging.info(f"[mark_invoice_as_paid_in_db] Tip #{tip.id} is now paid!")
        else:
            logging.info(f"[mark_invoice_as_paid_in_db] no match or already paid!")


# A basic logger for Breez events
class SDKListener(breez_sdk_liquid.EventListener):
    def on_event(self, event):
        if isinstance(event, Event.PaymentReceived):
            payment = event.payment
            if payment.status == PaymentStatus.Succeeded:
                mark_invoice_as_paid_in_db(payment.payment_hash)

def connect_breez(restore_only: bool = False):
    """
    Connects to the Breez node and sets up the Breez services globally.
    - If this is your first time, set restore_only=False to create a new node.
    - If you already have a node, set restore_only=True to reconnect.
    """

    global sdk_services

    # For dev, you might use a BIP39 test mnemonic or create your own
    # In production, store your real mnemonic in a safe place (not in code).
    # For now, let's assume you have it in environment:
    # e.g. MNEMONIC="abandon abandon abandon ... rocket manual"
    mnemonic = settings.BREEZ_MNEMONIC if hasattr(settings, 'BREEZ_MNEMONIC') else "donor vacuum copy narrow clown prosper another shift often robot torch below"

    seed = breez_sdk.mnemonic_to_seed(mnemonic)

    # Build the Breez config
    config = default_config(
        breez_api_key=settings.BREEZ_API_KEY,
        network=LiquidNetwork.MAINNET
    )
    config.working_dir = settings.BREEZ_WORKING_DIR

    # Connect request, specifying restore_only if you already have a node
    connect_request = ConnectRequest(config, seed)

    # This actually connects to the node (hosted on Greenlight).
    # Once done, Breez will handle LN channels, etc.
    try:
        sdk_services = breez_sdk_liquid.connect(connect_request, SDKListener())
        logging.info("Breez SDK connected successfully.")
    except Exception as e:
        logging.error(f"Error connecting to Breez: {e}")
        raise

# try:
#     connect_request = ConnectRequest(config, mnemonic)
#     sdk = connect(connect_request)
#     return sdk
# except Exception as error:
#     logging.error(error)
#     raise


def get_balance():
    """
    Returns the node's lightning and on-chain balance (in millisats).
    Will throw an error if connect_breez() hasn't been called yet.
    """
    if not sdk_services:
        raise RuntimeError("Breez SDK not connected yet. Call connect_breez() first.")

    node_state = sdk_services.node_info()
    ln_balance = node_state.channels_balance_msat
    onchain_balance = node_state.onchain_balance_msat
    return {
        "lightning_balance_msat": ln_balance,
        "onchain_balance_msat": onchain_balance
    }

def create_invoice(amount_sats: int, description: str = "Tip invoice"):
    """
    Creates a lightning invoice. Returns the BOLT11 invoice string.
    """
    if not sdk_services:
        raise RuntimeError("Breez SDK not connected yet. Call connect_breez() first.")

    amount_msat = amount_sats * 1000
    request = ReceivePaymentRequest(amount_msat, description)
    response = sdk_services.receive_payment(request)
    # response.ln_invoice is the BOLT11 invoice
    return (response.ln_invoice, response.payment_hash)

# def pay_invoice(invoice: str, amount_sats: int = None):
#     """
#     Pays a BOLT11 invoice. If the invoice doesn't specify an amount,
#     you can pass 'amount_sats'.
#     """
#     if not sdk_services:
#         raise RuntimeError("Breez SDK not connected yet. Call connect_breez() first.")

#     # If invoice already includes an amount, amount_msat can be omitted.
#     amount_msat = amount_sats * 1000 if amount_sats else None
#     req = SendPaymentRequest(
#         bolt11=invoice,
#         amount_msat=amount_msat,
#         # The next two params are optional
#         label="ZapZap Payment",
#         use_trampoline=True
#     )
#     try:
#         result = sdk_services.send_payment(req)
#         # 'result' includes payment_hash, payment_preimage, etc.
#         return result
#     except Exception as e:
#         logging.error(f"Failed to pay invoice: {e}")
#         raise

def pull_unpaid_invoices_since(last_timestamp: int):
    """
    Lists all payments (both sent and received).
    """
    if not sdk_services:
        raise RuntimeError("Breez SDK not connected yet. Call connect_breez() first.")

    req = ListPaymentsRequest(
        payment_type_filter=PaymentTypeFilter.Received,
        from_timestamp=last_timestamp,
        include_failures=False
    )

    new_payments = sdk_services.list_payments(req)
    count_marked = 0

    for p in new_payments:
        if p.status == PaymentStatus.Succeeded:
            mark_invoice_as_paid_in_db(p.payment_hash)
            count_marked += 1
    logging.info(f"[pull_unpaid_invoices_since] Marked {count_marked} new invoices as paid!")

