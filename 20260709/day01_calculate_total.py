from decimal import Decimal, ROUND_HALF_UP


ZERO_AMOUNT = Decimal("0.00")


def round_money(amount: Decimal) -> Decimal:
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_total(price: Decimal, quantity: int, discount: Decimal) -> Decimal:
    if price <= Decimal("0"):
        return ZERO_AMOUNT

    if quantity <= 0:
        return ZERO_AMOUNT

    if discount <= Decimal("0") or discount > Decimal("1"):
        return ZERO_AMOUNT

    amount = price * quantity * discount
    return round_money(amount)


if __name__ == "__main__":
    print(calculate_total(Decimal("2.00"), 8, Decimal("0.8")))
