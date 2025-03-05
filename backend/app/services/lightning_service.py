import logging
import threading

import breez_sdk
from breez_sdk import (
    ConnectRequest,
    EnvironmentType,
    EventListener,
    NodeConfig,
    default_config,
    mnemonic_to_seed,
)
from config import settings
from db import SessionLocal
from models.db import Tip, Tweet, User
from routes.sse import notify_clients_of_payment_status

# from services.twitter_service import post_reply_to_twitter_with_comment
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.getLogger().setLevel(logging.INFO)

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


def calculate_amount_to_send_sats(amount_sats: int):
    # fees are defined as 4 sats + 0.05% of the amount.
    # Given an amount, we need to subtract the fees to get the actual amount to send.
    fees = 4 + (amount_sats * 0.005)
    return int(amount_sats - fees)


def send_lnurl_payment(lnurl_address: str, amount_sats: int, sender_username: str):
    try:
        parsed_input = breez_sdk.parse_input(lnurl_address)
        if isinstance(parsed_input, breez_sdk.InputType.LN_URL_PAY):
            amount_msat = calculate_amount_to_send_sats(amount_sats) * 1000
            use_trampoline = True
            comment = f"⚡⚡ ZapZap from @{sender_username}"

            req = breez_sdk.LnUrlPayRequest(
                data=parsed_input.data,
                amount_msat=amount_msat,
                use_trampoline=use_trampoline,
                comment=comment,
            )

            pay_res = sdk_services.pay_lnurl(req)
            logging.info("LNURL Payment successful")
            payment_hash = pay_res.data.payment.details.data.payment_hash
            return payment_hash
            # return pay_res.data.payment.payment_hash
        else:
            logging.error("Provided input is not LNURL-PAY type.")
    except Exception as error:
        logging.error(f"Error sending LNURL payment: {error}")
        raise


def forward_payment_to_receiver(tip_id: int):
    with SessionLocal() as db:
        # Initial checks
        tip = db.query(Tip).filter(Tip.id == tip_id).first()
        if not tip:
            logging.error(f"Tip ID {tip_id} not found.")
            return None

        # Double-check paid status before proceeding
        if tip.paid_out:
            logging.warning(f"Tip {tip_id} is already marked as paid out. Skipping payment.")
            return tip.forward_payment_hash

        if not tip.paid_in:
            logging.error(f"Tip ID {tip_id} is not marked as paid.")
            return None

        if not tip.tweet:
            logging.error(f"Tweet ID {tip.tweet_id} not found.")
            return None

        receiver = tip.tweet.author
        sender = tip.sender

        # Only post reply if we haven't paid out yet
        # if not tip.paid_out:
        #     try:
        #         post_reply_to_twitter_with_comment(db, tip)
        #     except Exception as e:
        #         logging.warning(f"Failed to post Twitter reply for tip {tip_id}: {e}")
        # Continue with payment even if Twitter post fails

        if not receiver or not receiver.wallet_address:
            logging.error(f"Receiver @{receiver.twitter_username} not found or does not have wallet address.")
            return None

        address_str = receiver.wallet_address
        logging.info(f"Forwarding {tip.amount_sats} sats to @{receiver.twitter_username} at address {address_str}")

        # First attempt - original case as stored
        try:
            logging.info(f"[LNURL] Attempting LNURL pay for original case: {address_str}")
            payment_hash = send_lnurl_payment(address_str, tip.amount_sats, sender.twitter_username)

            # Recheck paid status before marking as paid
            db.refresh(tip)
            if tip.paid_out:
                logging.warning(f"Tip {tip_id} was marked as paid during processing. Skipping payment confirmation.")
                return tip.forward_payment_hash

            if payment_hash:
                tip.forward_payment_hash = payment_hash
                tip.paid_out = True
                db.commit()
                logging.info(f"Successfully forwarded {tip.amount_sats} sats to @{receiver.twitter_username}")
                return payment_hash
        except Exception as e:
            logging.info(f"Payment failed with original case, trying lowercase: {e}")

        # Second attempt - lowercase
        try:
            lowercase_address = address_str.lower()
            if lowercase_address == address_str:
                logging.info("Address is already lowercase, skipping second attempt")
                return None

            logging.info(f"[LNURL] Attempting LNURL pay for lowercase: {lowercase_address}")

            # Double check paid status again before second attempt
            db.refresh(tip)
            if tip.paid_out:
                logging.warning(f"Tip {tip_id} was marked as paid during processing. Skipping second attempt.")
                return tip.forward_payment_hash

            payment_hash = send_lnurl_payment(address_str, tip.amount_sats, sender.twitter_username)
            if payment_hash:
                tip.forward_payment_hash = payment_hash
                tip.paid_out = True
                db.commit()
                logging.info(
                    f"Successfully forwarded {tip.amount_sats} sats to @{receiver.twitter_username} using lowercase address"
                )
                return payment_hash
        except Exception as e:
            logging.error(f"Payment failed with both cases: {e}")

        logging.error(f"No payment options found for sending {tip.amount_sats} sats to @{receiver.twitter_username}")
        return None


def forward_pending_tips_for_user(user_id: int, db: Session):
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.wallet_address:
        logging.error(f"User ID {user_id} does not exist or lacks a wallet address")
        return
    pending_tips = (
        db.query(Tip)
        .join(Tweet, Tweet.id == Tip.tweet_id)
        .filter(
            Tweet.tweet_author == user.id,
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


class MyGreenlightListener(EventListener):
    def on_event(self, sdk_event):
        if isinstance(sdk_event, breez_sdk.BreezEvent.INVOICE_PAID):
            payment_hash = sdk_event.details.payment_hash
            logging.info(f"[MyGreenlightListener] Payment received, hash={payment_hash}")

            with SessionLocal() as db:
                tip = (
                    db.query(Tip)
                    .filter(Tip.ln_payment_hash == payment_hash)
                    .with_for_update()  # Lock the row
                    .first()
                )

                if not tip:
                    logging.warning(f"[MyGreenlightListener] Tip not found for hash={payment_hash}")
                    return

                if tip.paid_out:
                    logging.info(f"[MyGreenlightListener] Tip #{tip.id} already paid out, skipping.")
                    notify_clients_of_payment_status(payment_hash)  # Add notification
                    return

                was_unpaid = not tip.paid_in
                if was_unpaid:
                    tip.paid_in = True
                    db.commit()
                    logging.info(f"[MyGreenlightListener] Marked tip #{tip.id} as paid_in.")

                    # Notify clients that payment was received
                    notify_clients_of_payment_status(payment_hash)

                    # Only spawn forwarding thread if we just marked it as paid
                    t = threading.Thread(target=forward_payment_to_receiver, args=(tip.id,))
                    t.start()
                    logging.info(f"[MyGreenlightListener] Spawned thread to forward tip #{tip.id}")
                else:
                    logging.info(f"[MyGreenlightListener] Tip #{tip.id} was already paid_in, skipping.")
                    notify_clients_of_payment_status(payment_hash)  # Add notification


class BreezLogger(breez_sdk.LogStream):
    def log(self, log):
        logging.basicConfig(level=logging.DEBUG)
        if log.level in ("ERROR", "WARNING"):
            print("Received log [", log.level, "]: ", log.line)


def init_breez_logging():
    breez_sdk.set_log_stream(BreezLogger())


def connect_breez(restore_only: bool = True):
    """
    Connects to the Breez node and sets up the Breez services globally.
    - If this is your first time, set restore_only=False to create a new node.
    - If you already have a node, set restore_only=True to reconnect.
    """

    global sdk_services
    seed = mnemonic_to_seed(settings.BREEZ_MNEMONIC)

    # Build the Breez config
    config = default_config(
        EnvironmentType.PRODUCTION,
        settings.BREEZ_API_KEY,
        NodeConfig.GREENLIGHT(
            breez_sdk.GreenlightNodeConfig(partner_credentials=None, invite_code=settings.BREEZ_GREENLIGHT_INVITE)
        ),
    )
    config.working_dir = settings.BREEZ_WORKING_DIR

    try:
        my_listener = MyGreenlightListener()
        connect_request = ConnectRequest(config, seed, restore_only=restore_only)
        sdk_services = breez_sdk.connect(connect_request, my_listener)
        logging.info("Breez SDK connected successfully.")
        return True

    except Exception as e:
        logging.error(f"Error connecting to Breez: {e}")
        sdk_services = None
        return False


def create_invoice(amount_sats: int, description: str = "Tip invoice"):
    """
    Creates a lightning invoice. Returns the BOLT11 invoice string.
    """
    if not sdk_services:
        raise RuntimeError("Breez SDK not connected yet. Call connect_breez() first.")

    req = breez_sdk.ReceivePaymentRequest(amount_sats * 1000, description=description)

    res = sdk_services.receive_payment(req)
    try:
        bolt11_invoice = res.ln_invoice.bolt11  # Access the ln_invoice attribute
        payment_hash = res.ln_invoice.payment_hash  # Access the payment_hash attribute
    except AttributeError as e:
        print(f"Error accessing response attributes: {e}")
        raise RuntimeError("Failed to parse response from receive_payment")

    # Return the invoice and payment hash
    return payment_hash, bolt11_invoice


# def mark_invoice_as_paid_in_db(invoice_or_hash: str):
#     with SessionLocal() as db:
#         tip = db.query(Tip).filter(Tip.ln_payment_hash == invoice_or_hash).first()
#         # if not tip:
#         #     tip = db.query(Tip).filter(Tip.bolt11_invoice == invoice_or_hash).first()
#         if not tip:
#             return

#         if not tip.paid_in:
#             tip.paid_in = True
#             db.commit()
#             logging.info(f"[mark_invoice_as_paid_in_db] Tip #{tip.id} is now paid!")

#         if tip.tweet and tip.tweet.author:
#             recipient_twitter_username = tip.tweet.author.twitter_username
#         else:
#             logging.error(f"[mark_invoice_as_paid_in_db] Tip #{tip.id} has no recipient Twitter username.")
#             recipient_twitter_username = None

#         if not tip.paid_out:
#             try:
#                 payment_hash = forward_payment_to_receiver(tip.id)
#                 if payment_hash:
#                     tip.forward_payment_hash = payment_hash
#                     tip.paid_out = True
#                     db.commit()
#                     logging.info(
#                         f"[mark_invoice_as_paid_in_db] Forwarded {tip.amount_sats} sats to receiver @{recipient_twitter_username}. Tip #{tip.id} marked as paid out."
#                     )
#                 else:
#                     logging.error(f"[mark_invoice_as_paid_in_db] Forwarding payment failed for Tip #{tip.id}")
#             except Exception as e:
#                 logging.error(f"[mark_invoice_as_paid_in_db] Failed to forward payment for Tip #{tip.id}: {e}")
#         else:
#             logging.info("[mark_invoice_as_paid_in_db] no match or already paid!")
