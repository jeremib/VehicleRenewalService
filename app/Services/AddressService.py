import json
import logging
import urllib.parse
import urllib.request

CENSUS_GEOCODER_URL = "https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress"


def is_in_city_limits(address: str, timeout: float = 5.0):
    """Return True/False if Census matches the address to an incorporated place,
    or None when the lookup is inconclusive (network failure / no match)."""
    params = {
        "address": address,
        "benchmark": "Public_AR_Current",
        "vintage": "Census2020_Current",
        "layers": "Incorporated_Places",
        "format": "json",
    }
    url = f"{CENSUS_GEOCODER_URL}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            data = json.load(resp)
    except Exception as e:
        logging.error(f"Census geocoder lookup failed for {address!r}: {e}")
        return None

    matches = data.get("result", {}).get("addressMatches") or []
    if not matches:
        logging.info(f"Census geocoder returned no matches for {address!r}")
        return None
    places = matches[0].get("geographies", {}).get("Incorporated Places", []) or []
    in_limits = bool(places)
    place_name = places[0].get("NAME") if in_limits else None
    logging.info(
        f"Census geocoder: {address!r} in_city_limits={in_limits} place={place_name!r}"
    )
    return in_limits
