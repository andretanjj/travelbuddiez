import requests


FRANKFURTER_BASE_URL = "https://api.frankfurter.dev/v2"

# Keep the first version intentionally limited to currencies
# that are relevant for TravelBuddiez users.
SUPPORTED_CURRENCIES = {
    "SGD",
    "USD",
    "EUR",
    "GBP",
    "JPY",
    "KRW",
    "MYR",
    "AUD",
}


def get_exchange_rate(
    from_currency: str,
    to_currency: str,
):
    """
    Fetches the latest exchange rate from Frankfurter.

    Example:
    USD -> SGD

    Response shape:
    {
        "date": "2026-08-07",
        "base": "USD",
        "quote": "SGD",
        "rate": 1.28
    }
    """

    from_code = from_currency.upper()
    to_code = to_currency.upper()

    if from_code not in SUPPORTED_CURRENCIES:
        raise ValueError(
            f"Unsupported source currency: {from_code}"
        )

    if to_code not in SUPPORTED_CURRENCIES:
        raise ValueError(
            f"Unsupported target currency: {to_code}"
        )

    # No API request is needed when both currencies are the same.
    if from_code == to_code:
        return {
            "date": None,
            "base": from_code,
            "quote": to_code,
            "rate": 1.0,
        }

    url = (
        f"{FRANKFURTER_BASE_URL}/rate/"
        f"{from_code}/{to_code}"
    )

    response = requests.get(
        url,
        timeout=10,
    )

    if not response.ok:
        raise RuntimeError(
            "Currency conversion service failed: "
            f"{response.status_code} {response.text}"
        )

    data = response.json()

    return {
        "date": data.get("date"),
        "base": data["base"],
        "quote": data["quote"],
        "rate": float(data["rate"]),
    }