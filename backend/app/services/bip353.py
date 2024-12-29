import dns.resolver
import re

def resolve_user_domain_to_bolt12(user_domain):
    """
    Resolves a user@domain format to a BOLT-12 lno1 format using DNS.

    test with simon@imaginator.com or a phoenix wallet "human readable address"

    :param user_domain: Input in the user@domain format.
    :return: BOLT-12 lno1 address as a string or None if resolution fails.
    """
    try:
        # Extract the user and domain
        user, domain = user_domain.split("@")
        
        # Formulate the DNS label for TXT record lookup
        txt_query = f"{user}.user._bitcoin-payment.{domain}"

        # Perform the DNS TXT record query
        answers = dns.resolver.resolve(txt_query, 'TXT')

        # Join all TXT record strings together
        lno_address = ''.join([''.join(r.decode('utf-8') for r in record.strings) for record in answers]).replace("bitcoin:?lno=", "", 1)  # Return the complete joined lno1 address
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

def is_bolt12_address(address):
    """
    Checks if a given string is in the BOLT-12 lno1 format.

    :param address: The string to check.
    :return: True if it is in the BOLT-12 lno1 format, False otherwise.
    """
    return address.lower().startswith("lno1")

def is_user_domain_format(input_str):
    """
    Checks if a given string is in the user@domain format.

    :param input_str: The string to check.
    :return: True if it is in the user@domain format, False otherwise.
    """
    return re.match(r"^[^@]+@[a-zA-Z0-9.-]+$", input_str) is not None

def resolve_input(input_str):
    """
    Resolves the input string to a BOLT-12 lno1 address.
    If the input is already in lno1 format, it validates and returns it.

    :param input_str: The input string (user@domain or BOLT-12 address).
    :return: BOLT-12 lno1 address as a string or None if resolution/validation fails.
    """
    if is_bolt12_address(input_str):
        print(f"Input is already a valid BOLT-12 address: {input_str}")
        return input_str
    elif is_user_domain_format(input_str):
        print(f"Input is in user@domain format, attempting to resolve: {input_str}")
        return resolve_user_domain_to_bolt12(input_str)
    else:
        print(f"Invalid input format: {input_str}")
        return None

# Example usage
if __name__ == "__main__":
    input_str = "simon@imaginator.com"  # Replace with the actual input (user@domain or BOLT-12 address)
    result = resolve_input(input_str)

    if result:
        print(f"Resolved BOLT-12 address: {result}")
    else:
        print(f"Failed to resolve BOLT-12 address for input: {input_str}")
