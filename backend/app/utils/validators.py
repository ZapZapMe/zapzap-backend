import re
from typing import Optional


class WalletAddressValidator:
    # Using the more restrictive regex that ensures proper email format
    EMAIL_REGEX = re.compile(
        r'^[A-Za-z0-9_!#$%&\'*+/=?`{|}~^-]+(?:\.[A-Za-z0-9_!#$%&\'*+/=?`{|}~^-]+)*'
        r'@'
        r'(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,6}$'
    )

    @classmethod
    def validate(cls, wallet_address: Optional[str]) -> tuple[bool, Optional[str]]:
        """
        Validates a wallet address and returns (is_valid, error_message).
        Preserves original case.
        """
        if not wallet_address:
            return True, None  # Allow None/empty as it's optional
            
        # Remove any whitespace
        wallet_address = wallet_address.strip()
        
        # Basic length check
        if len(wallet_address) > 254:
            return False, "Wallet address is too long"
            
        # Check for valid format using regex
        if not cls.EMAIL_REGEX.match(wallet_address):
            return False, "Invalid wallet address format - must be a valid email address"
            
        return True, None