import logging
from datetime import datetime
import lnurl
import breez_sdk
from breez_sdk import (
    ConnectRequest,
    EnvironmentType,
    EventListener,
    ListPaymentsRequest,
    NodeConfig,
    Payment,
    PaymentStatus,
    PaymentType,
    PaymentTypeFilter,
    ReceivePaymentRequest,
    SendPaymentRequest,
    default_config,
    mnemonic_to_seed,
    parse_input,
    parse_invoice,
)
from config import settings
from db import SessionLocal
from models.tip import Tip
from models.user import User
from services.bip353 import resolve_recipient_via_bip353
from sqlalchemy.orm import Session

# from sqlalchemy.orm import Session


# Optional: define a global variable for 'sdk_services'
sdk_services = None


def send_bolt12_payment(bolt12_offer: str, amount_sats: int):
    pass
    # ross_bolt12 = "lno1zrxq8pjw7qjlm68mtp7e3yvxee4y5xrgjhhyf2fxhlphpckrvevh50u0qtn2mq3gzvt8mkq4fy7vgt34s3kkdpllgshz3ak3d8st0texhm2hqqszvedh6tvvyt2zyvcl39chzqja08y3zu27f8jjl7mgyyp2kw5da6cqqvc3naftwk24xr90uqhwqv2p2znatq2tgh63ny3vd4slykgcx87ftuh28jwpvygshf34gfc8ywnkxlw89dh2qvmz9da8dw6nx5gty895tllv3t2lzk02l7vzna3m9dnpphjftncwvqqs4zrs72t38qscfe49vnwwmucwhg"

    # try:
    #     optional_amount = PayAmount.RECEIVER(amount_sats)
    #     prepare_req = PrepareSendRequest(destination=bolt12_offer, amount=optional_amount)
    #     prepare_res = sdk_services.prepare_send_payment(prepare_req)
    #     logging.info(f"Prepared to send {amount_sats} to {bolt12_offer}. Estimated fees: {prepare_res.fees_sat} sats")
    #     send_req = SendPaymentRequest(prepare_res)
    #     print("SEND REQUEST", send_req)
    #     send_res = sdk_services.send_payment(send_req)
    #     print("SEND RESPONSE", send_res)
    #     logging.info(f"Payment sent successfully. Payment Hash: {send_res.payment}")
    #     return send_res.payment
    # except Exception as e:
    #     logging.error(f"Error creating PayAmount: {e}")
    #     return None


def send_lnurl_payment(lnurl_address: str, amount_sats: int):
    try:
        parsed_input = breez_sdk.parse_input(lnurl_address)
        if isinstance(parsed_input, breez_sdk.InputType.LN_URL_PAY):
            amount_msat = amount_sats * 1000
            use_trampoline = True
            comment = "test"

            req = breez_sdk.LnUrlPayRequest(
                ln_url_pay=parsed_input.data,
                amount_msat=amount_msat,
                use_trampoline=use_trampoline,
                comment=comment,
            )

            pay_res = sdk_services.pay_lnurl(req)
            logging.info("LNURL Payment successful")
            return pay_res.payment_hash
        else:
            logging.error("Provided input is not LNURL-PAY type.")
    except Exception as error:
        print(f"Issue with LNURL payment: {error}")
        logging.error(error)
        raise


def forward_payment_to_receiver(tip_id: int):
    with SessionLocal() as db:
        tip = db.query(Tip).filter(Tip.id == tip_id).first()
        if not tip:
            logging.error(f"Tip ID {tip_id} not found.")
            return None
        if not tip.paid_in:
            logging.error(f"Tip ID {tip_id} is not marked as paid.")
            return None

        receiver = db.query(User).filter(User.twitter_username == tip.recipient_twitter_username).first()
        if not receiver or not receiver.wallet_address:
            logging.error(f"Receiver @{tip.recipient_twitter_username} not found or does not have waller address.")
            return None

        address_str = receiver.wallet_address
        logging.info(f"Forwarding {tip.amount_sats} sats to @{tip.recipient_twitter_username} at address {address_str}")

        bolt12_offer = resolve_recipient_via_bip353(address_str)
        if bolt12_offer:
            logging.info(f"[BIP353] Resolved BOLT12 offer: {bolt12_offer}")
            payment_hash = send_bolt12_payment(bolt12_offer, tip.amount_sats)
        else:
            logging.error(f"[LNURL] Attempting LNURL pay for {address_str}")
            payment_hash = send_lnurl_payment(address_str, tip.amount_sats)

        if payment_hash:
            tip.forward_payment_hash = payment_hash
            tip.paid_out = True
            db.commit()
            logging.info(f"Successfully forwarded {tip.amount_sats} sats to @{tip.recipient_twitter_username}")
            return payment_hash
        else:
            logging.error(
                f"No payment options found for sending {tip.amount_sats} sats to @{tip.recipient_twitter_username}"
            )
            return None


def forward_pending_tips_for_user(user_id: int, db: Session):
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.wallet_address:
        logging.error(f"User ID {user_id} does not exist or lacks a BOLT12 address")
        return
    pending_tips = (
        db.query(Tip)
        .filter(
            Tip.recipient_twitter_username == user.twitter_username,
            Tip.paid_in.is_(True),
            Tip.paid_out.is_(False),
        )
        .all()
    )

    if not pending_tips:
        logging.info(f"No pending tips to forward to the user {user.twitter_username}")
        return

    logging.info(f"Found {len(pending_tips)} pending tips for user {user.twitter_username}")

    for tip in pending_tips:
        try:
            payment_hash = forward_payment_to_receiver(tip.id)
            if payment_hash:
                tip.forward_payment_hash = payment_hash
                tip.paid_out = True
                db.commit()
                logging.info(
                    f"Successfully forwarded {tip.amount_sats} sats for the Tip #{tip.id} to {user.wallet_address}"
                )
            else:
                logging.error(f"Failed to forward Tip #{tip.id} for user {user.twitter_username}")

        except Exception as e:
            logging.error(f"Exception occured while forwarding tip #{tip.id}: {e}")


def mark_invoice_as_paid_in_db(invoice_or_hash: str):
    with SessionLocal() as db:
        tip = db.query(Tip).filter(Tip.ln_payment_hash == invoice_or_hash).first()
        if not tip:
            tip = db.query(Tip).filter(Tip.bolt11_invoice == invoice_or_hash).first()
        if not tip:
            return

        if tip and not tip.paid_in:
            tip.paid_in = True
            db.commit()
            logging.info(f"[mark_invoice_as_paid_in_db] Tip #{tip.id} is now paid!")

        if not tip.paid_out:
            try:
                payment_hash = forward_payment_to_receiver(tip.id)
                if payment_hash:
                    tip.forward_payment_hash = payment_hash
                    tip.paid_out = True
                    db.commit()
                    logging.info(
                        f"[mark_invoice_as_paid_in_db] Forwarded {tip.amount_sats} sats to receiver @{tip.recipient_twitter_username}. Tip #{tip.id} marked as paid out."
                    )
                else:
                    logging.error(f"[mark_invoice_as_paid_in_db] Forwarding payment failed for Tip #{tip.id}")
            except Exception as e:
                logging.error(f"[mark_invoice_as_paid_in_db] Failed to forward payment for Tip #{tip.id}: {e}")
        else:
            logging.info("[mark_invoice_as_paid_in_db] no match or already paid!")


class MyGreenlightListener(EventListener):
    def on_event(self, sdk_event):
        logging.info(f"[MyGreenlightListener] Received event: {sdk_event}")
        print(f"[MyGreenlightListener] Received event: {sdk_event}")
        # if isinstance(sdk_event, breez_sdk.SdkEvent.PAYMENT_WAITING_CONFIRMATION):
        #     payment = sdk_event.details
        #     if payment.destination:
        #         payment_invoice = payment.destination
        #         mark_invoice_as_paid_in_db(payment_invoice)
        #         logging.info(f"[MyGreenlightListener] Marked {payment_invoice} as paid in DB")
        #         print(f"[MyGreenlightListener] Marked {payment_invoice} as paid in DB")


# def add_greenlight_event_listener():
#     global sdk_services
#     if not sdk_services:
#         raise RuntimeError("Greenlight SDK not connected yet. Call connect_breez() first.")

#     listener = MyGreenlightListener()
#     listener_id = sdk_services.add_event_listener(sdk_services, listener)
#     logging.info(f"Event listener initialized with ID: {listener_id}")
#     return listener_id


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


class MyLogStream(breez_sdk.LogStream):
    def log(self, l):
        logging.basicConfig(level=logging.DEBUG)
        if l.level in ("ERROR"):
            print("Received log [", l.level, "]: ", l.line)


def connect_breez(restore_only: bool = False):
    """
    Connects to the Breez node and sets up the Breez services globally.
    - If this is your first time, set restore_only=False to create a new node.
    - If you already have a node, set restore_only=True to reconnect.
    """

    global sdk_services
    breez_sdk.set_log_stream(MyLogStream())

    # For dev, you might use a BIP39 test mnemonic or create your own
    # In production, store your real mnemonic in a safe place (not in code).
    # For now, let's assume you have it in environment:
    # e.g. MNEMONIC="abandon abandon abandon ... rocket manual"
    mnemonic = settings.BREEZ_MNEMONIC
    seed = mnemonic_to_seed(mnemonic)

    invite_code = settings.BREEZ_GREENLIGHT_INVITE

    # Build the Breez config
    config = default_config(
        EnvironmentType.PRODUCTION,
        settings.BREEZ_API_KEY,
        NodeConfig.GREENLIGHT(breez_sdk.GreenlightNodeConfig(partner_credentials=None, invite_code=invite_code)),
    )
    config.working_dir = settings.BREEZ_DATA_PATH

    try:
        print("I am trying")
        my_listener = MyGreenlightListener()
        connect_request = ConnectRequest(config, seed, restore_only=restore_only)
        sdk_services = breez_sdk.connect(connect_request, my_listener)
        print("Breez Connected Successfully")
        info = sdk_services.node_info()
        print("Channels balance:", info.channels_balance_msat)
        print("On-chain balance:", info.onchain_balance_msat)
        lsp_id = sdk_services.lsp_id()
        lsp_info = sdk_services.lsp_info()
        print("LSP ID:", lsp_id)
        print("LSP Info:", lsp_info)


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


# def get_balance():
#     try:
#         info = sdk_services.get_info()
#         balance_sats = info.balance_sat
#         pending_sats = info.pending_send_sat
#         pending_receive_sats = info.pending_receive_sat
#     except Exception as error:
#         logging.error(error)
#         raise

# if not sdk_services:
#     raise RuntimeError("Breez SDK not connected yet. Call connect_breez() first.")

# node_state = sdk_services.node_info()
# ln_balance = node_state.channels_balance_msat
# onchain_balance = node_state.onchain_balance_msat
# return {
#     "lightning_balance_msat": ln_balance,
#     "onchain_balance_msat": onchain_balance,
# }


def create_invoice(tweet_url: str, amount_sats: int, description: str = "Tip invoice"):
    """
    Creates a lightning invoice. Returns the BOLT11 invoice string.
    """
    if not sdk_services:
        raise RuntimeError("Breez SDK not connected yet. Call connect_breez() first.")

    req = breez_sdk.ReceivePaymentRequest(amount_sats*1000, description=description)

    res = sdk_services.receive_payment(req)
    print("RES", res)
    
    try:
        bolt11_invoice = res.ln_invoice.bolt11  # Access the ln_invoice attribute
        payment_hash = res.ln_invoice.payment_hash  # Access the payment_hash attribute
    except AttributeError as e:
        print(f"Error accessing response attributes: {e}")
        raise RuntimeError("Failed to parse response from receive_payment")

    # Return the invoice and payment hash
    return bolt11_invoice, payment_hash, 0


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



def extract_payment_hash(invoice: str) -> str:
    decoded_invoice = lnurl.decode(invoice)
    payment_hash = decoded_invoice.get("payment_hash", None)

    if payment_hash:
        return payment_hash
    else:
        raise ValueError("Payment hash not found in the invoice")


def pull_unpaid_invoices_since(last_timestamp: datetime):
    """
    Lists all payments (both sent and received).
    """
    if not sdk_services:
        raise RuntimeError("Breez SDK not connected yet. Call connect_breez() first.")

    last_timestamp = 0
    print("Last timestamp: ", last_timestamp)

    req = breez_sdk.ListPaymentsRequest(
        filters=[breez_sdk.PaymentTypeFilter.SENT],
        from_timestamp=last_timestamp,
    )
    new_payments = sdk_services.list_payments(req)
    print("New payments: ", new_payments)
    count_marked = 0

    for p in new_payments:
        if p.status == breez_sdk.PaymentStatus.COMPLETE:
            bolt11_of_this_payment = p.destination
            mark_invoice_as_paid_in_db(bolt11_of_this_payment)
            count_marked += 1
    logging.info(f"[pull_unpaid_invoices_since] Marked {count_marked} new invoices as paid!")
