DISCLAIMER = (
    "**DISCLAIMER:** Purchasing this does _not_ guarantee your purchase will be added. "
    "It must be approved. Upon rejection, your coins will be refunded."
)


def emoji_price(total_slots: int, used_slots: int) -> int:
    """Increase price as more slots are filled."""
    avaliable = total_slots - used_slots
    return 12 ** (1 - avaliable) + 50


print(emoji_price(250, 0))
