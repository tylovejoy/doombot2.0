DISCLAIMER = (
    "**DISCLAIMER:** Purchasing this does _not_ guarantee your purchase will be added. "
    "It must be approved. Upon rejection, your coins will be refunded."
)


def emoji_price(total_slots: int, used_slots: int) -> int:
    """Increase price as more slots are filled."""
    available = total_slots - used_slots
    return 12 ** (1 - available) + 50
