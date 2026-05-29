# mock advisory for now
def get_advisory(country_code: str) -> str:
    advisories = {
        "SGP": "No major travel advisory available in the current mock data.",
        "JPN": "Monitor weather warnings and regional travel notices before travelling.",
        "IDN": "Check for natural disaster warnings before travelling to affected regions.",
    }

    return advisories.get(
        country_code,
        "No advisory information is available for this destination yet.",
    )