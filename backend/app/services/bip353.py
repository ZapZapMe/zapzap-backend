import urllib.parse

import dns.resolver
import requests

# we store the payout address as user@domain in the database
# when it comes time to do a payment(user@domain):
#   if
#       recipient resolves via bip353 # bolt12
#           do a sdk.prepare_send_payment
#   else:
#       resolve_recipient_via_lud16 # lnurl
#           do a sdk.lnurl_pay


def resolve_recipient_via_bip353(user_domain):
    try:
        # Extract the user and domain
        user, domain = user_domain.split("@")

        # Formulate the DNS label for TXT record lookup
        txt_query = f"{user}.user._bitcoin-payment.{domain}"

        # Perform the DNS TXT record query
        answers = dns.resolver.resolve(txt_query, "TXT")

        # Join all TXT record strings together (255 character max)
        bip21_uri = "".join(["".join(r.decode("utf-8") for r in record.strings) for record in answers])

        # bitcoin:?lno=lno1XXXXXXXX
        parsed_bip21 = parse_bip21(bip21_uri)
        lno_address = parsed_bip21.get("lno")
        if lno_address:
            return lno_address
        else:
            print("No valid bitcoin records found.")
            return None

    except dns.resolver.NoAnswer:
        print(f"No TXT record found for {txt_query}")
    except dns.resolver.NXDOMAIN:
        print(f"Domain {domain} does not exist.")
    except Exception as e:
        print(f"Error resolving {user_domain}: {e}")

    return None


def resolve_recipient_via_lud16(user_domain):
    try:
        # Split the identifier into username and domain
        if "@" not in user_domain:
            return False

        username, domain = user_domain.split("@", 1)

        # Construct the LUD-16 lookup URL
        url = f"https://{domain}/.well-known/lnurlp/{username}"
        print(f"{url}")
        # Perform the HTTP GET request
        response = requests.get(url, timeout=2)

        # Check for a valid response with required fields
        if response.status_code == 200:
            metadata = response.json()
            if "callback" in metadata and "minSendable" in metadata and "maxSendable" in metadata:
                return user_domain
        return False
    except (requests.RequestException, ValueError):
        return False


def parse_bip21(uri):
    # Parse the BIP21 URI
    parsed = urllib.parse.urlparse(uri)

    # Ensure it's a Bitcoin URI
    if parsed.scheme != "bitcoin":
        raise ValueError("Invalid BIP21 URI: Missing 'bitcoin' scheme")

    # Extract the address and query components
    address = parsed.path
    query_params = urllib.parse.parse_qs(parsed.query)

    # Check if 'lno' exists
    lno = query_params.get("lno", [None])[0]

    return {"lno": lno}


def resolve_payout_method(user_domain):
    # Attempt to resolve the BOLT-12 address for the given user_domain
    lno_address = resolve_recipient_via_bip353(user_domain)
    if lno_address:
        # If the resolution is successful, prepare to send payment via BOLT-12
        print(f"Resolved BOLT-12 address for {user_domain}: {lno_address}")
        return lno_address
        # then we would send using sdk.prepare_send_payment(lno_address)

    lnurl_address = resolve_recipient_via_lud16(user_domain)
    if lnurl_address:
        print(f"Resolved LNURL address for {user_domain}: {lnurl_address}")
        return user_domain

    print(f"Failed to resolve payout method for {user_domain}")
    return None


# Example usage
if __name__ == "__main__":
    input_list = ["simon@imaginator.com", "imaginator@strike.me", "invalid@example.com"]
    for user in input_list:
        result = resolve_payout_method(user)
