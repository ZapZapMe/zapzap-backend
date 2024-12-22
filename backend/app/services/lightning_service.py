from datetime import datetime
import logging

from config import settings
import breez_sdk_liquid
from breez_sdk_liquid import (
    GetInfoResponse,
    PrepareReceiveRequest,
    PaymentMethod,
    ReceivePaymentRequest,
    ListPaymentsRequest,
    PaymentType,
    PaymentState,
    BindingLiquidSdk,
    ConnectRequest,
    default_config,
    LiquidNetwork,
    SdkEvent)
from db import SessionLocal
from models.tip import Tip
import lnurl


# from sqlalchemy.orm import Session


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
            logging.info(f"[mark_invoice_as_paid_in_db] Tip #{tip.temp_id} is now paid!")
        else:
            logging.info(f"[mark_invoice_as_paid_in_db] no match or already paid!")


class SdkListener(breez_sdk_liquid.EventListener):
    def on_event(sdk_event: SdkEvent):
        logging.debug("Received event ", sdk_event)
        print("Received event ", sdk_event)

def add_event_listener(sdk: BindingLiquidSdk, listener: SdkListener):
    try:
        listener_id = sdk.add_event_listener(listener)
        logging.info(f"Listener successfully added with ID: {listener_id}")
        return listener_id
    except Exception as error:
        logging.error(error)
        raise
        
class MyNodelessListener(SdkListener):
    def on_event(self, sdk_event: SdkEvent):
        logging.info(f"[MyNodelessListener] Received event: {sdk_event}")
        print(f"[MyNodelessListener] Received event: {sdk_event}")
        if isinstance(sdk_event, breez_sdk_liquid.SdkEvent.PAYMENT_SUCCEEDED):
            payment = sdk_event.details
            if payment.destination:
                payment_invoice = payment.destination
                mark_invoice_as_paid_in_db(payment_invoice)
                logging.info(f"[MyNodelessListener] Marked {payment_invoice} as paid in DB")
                print(f"[MyNodelessListener] Marked {payment_invoice} as paid in DB")



def add_liquid_event_listener():
    global sdk_services
    if not sdk_services:
        raise RuntimeError("Nodeless SDK not connected yet. Call connect_breez() first.")

    listener = MyNodelessListener()
    listener_id = add_event_listener(sdk_services, listener)
    logging.info(f"Event listener initialized with ID: {listener_id}")
    return listener_id


# def add_event_listener(sdk: BindingLiquidSdk, listener: SDKListener):
#     try:
#         listener_id = sdk.add_event_listener(listener)
#         logging.info(f"Listener added with ID: {listener_id}")
#         return listener_id

#     except Exception as error:
#         logging.error(error)
#         raise

#         if isinstance(event, Event.PaymentReceived):
#             payment = event.payment
#             if payment.status == PaymentStatus.Succeeded:
#                 mark_invoice_as_paid_in_db(payment.payment_hash)


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
    mnemonic = (
        settings.BREEZ_MNEMONIC
        if hasattr(settings, "BREEZ_MNEMONIC")
        else "donor vacuum copy narrow clown prosper another shift often robot torch below"
    )

    # Build the Breez config
    config = breez_sdk_liquid.default_config(
        breez_api_key=settings.BREEZ_API_KEY,
        network=breez_sdk_liquid.LiquidNetwork.MAINNET,
    )
    config.working_dir = settings.BREEZ_WORKING_DIR

    # Connect request, specifying restore_only if you already have a node
    connect_request = breez_sdk_liquid.ConnectRequest(config, mnemonic)

    # This actually connects to the node (hosted on Greenlight).
    # Once done, Breez will handle LN channels, etc.
    try:
        sdk_services = breez_sdk_liquid.connect(connect_request)
        print("Breez Connected Successfully")
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
    try: 
        info = sdk_services.get_info()
        balance_sats = info.balance_sat
        pending_sats = info.pending_send_sat
        pending_receive_sats = info.pending_receive_sat
    except Exception as error:
        logging.error(error)
        raise




    # if not sdk_services:
    #     raise RuntimeError("Breez SDK not connected yet. Call connect_breez() first.")

    # node_state = sdk_services.node_info()
    # ln_balance = node_state.channels_balance_msat
    # onchain_balance = node_state.onchain_balance_msat
    # return {
    #     "lightning_balance_msat": ln_balance,
    #     "onchain_balance_msat": onchain_balance,
    # }


def create_invoice(amount_sats: int, description: str = "Tip invoice"):
    """
    Creates a lightning invoice. Returns the BOLT11 invoice string.
    """
    if not sdk_services:
        raise RuntimeError("Breez SDK not connected yet. Call connect_breez() first.")

    prepare_req = PrepareReceiveRequest(
        payment_method=PaymentMethod.LIGHTNING, payer_amount_sat=amount_sats
    )


    prepare_resp = sdk_services.prepare_receive_payment(prepare_req)
    
    invoice_fee = prepare_resp.fees_sat

    logging.info(f"[create invoice] LN fees estimated: {invoice_fee} sats")

    receive_req = ReceivePaymentRequest(
        prepare_response=prepare_resp,
        description="Tip from anonymous",
        use_description_hash=False,
    )

    receive_res = sdk_services.receive_payment(receive_req)

    bolt11_invoice = receive_res.destination

    # amount_msat = amount_sats * 1000
    # request = breez_sdk_liquid.ReceivePaymentRequest(amount_msat, description)
    # response = sdk_services.receive_payment(request)
    # response.ln_invoice is the BOLT11 invoice
    return (bolt11_invoice, None, invoice_fee)


# try:
#     # Set the invoice amount you wish the payer to send, which should be within the above limits
#     prepare_request = PrepareReceiveRequest(PaymentMethod.LIGHTNING, 5_000)
#     prepare_response = sdk.prepare_receive_payment(prepare_request)

#     # If the fees are acceptable, continue to create the Receive Payment
#     receive_fees_sat = prepare_response.fees_sat
#     logging.debug("Fees: ", receive_fees_sat, " sats")
#     return prepare_response
# except Exception as error:
#     logging.error(error)
#     raise


def pull_unpaid_invoices_since(last_timestamp: datetime):
    """
    Lists all payments (both sent and received).
    """
    if not sdk_services:
        raise RuntimeError("Breez SDK not connected yet. Call connect_breez() first.")

    req = breez_sdk_liquid.ListPaymentsRequest(
        [breez_sdk_liquid.PaymentType.RECEIVE],
        from_timestamp=last_timestamp,
        offset=0,
        limit=50,
    )
    new_payments = sdk_services.list_payments(req)
    count_marked = 0

    for p in new_payments:
        if p.status == breez_sdk_liquid.PaymentState.COMPLETE:
            print("Payment paid when application starts")
            bolt11_of_this_payment = p.destination
            mark_invoice_as_paid_in_db(bolt11_of_this_payment)
            count_marked += 1
    logging.info(
        f"[pull_unpaid_invoices_since] Marked {count_marked} new invoices as paid!"
    )


def extract_payment_hash(invoice: str) -> str:
    decoded_invoice = lnurl.decode(invoice)
    payment_hash = decoded_invoice.get("payment_hash", None)
    
    if payment_hash:
        return payment_hash
    else:
        raise ValueError("Payment hash not found in the invoice")
