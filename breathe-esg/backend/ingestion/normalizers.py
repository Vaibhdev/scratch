"""
Unit normalization and conversion utilities for emissions activity data.

Conversion factors are sourced from standard references:
- Fuel densities: IPCC 2006 Guidelines, Volume 2, Table 1.2
- Airport coordinates: Major airports hardcoded for distance calculation
- Haversine formula for great-circle distance between airport pairs
"""

import math
from decimal import Decimal, ROUND_HALF_UP

# ---------------------------------------------------------------------------
# Fuel density factors (kg per liter at 15°C)
# Source: IPCC 2006, Volume 2, Chapter 1, Table 1.2
# ---------------------------------------------------------------------------
FUEL_DENSITIES = {
    "diesel": Decimal("0.832"),      # EN 590 diesel
    "petrol": Decimal("0.745"),      # Gasoline / Motor Spirit
    "gasoline": Decimal("0.745"),
    "heating_oil": Decimal("0.840"), # Light heating oil (EL)
    "lpg": Decimal("0.510"),         # Liquefied Petroleum Gas
    "kerosene": Decimal("0.800"),
}

# ---------------------------------------------------------------------------
# Unit conversion functions
# ---------------------------------------------------------------------------

def liters_to_kg(liters: Decimal, fuel_type: str) -> Decimal:
    """Convert liters to kilograms using fuel density."""
    density = FUEL_DENSITIES.get(fuel_type.lower(), Decimal("0.800"))
    return (liters * density).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def gallons_to_liters(gallons: Decimal) -> Decimal:
    """Convert US gallons to liters."""
    return (gallons * Decimal("3.78541")).quantize(
        Decimal("0.0001"), rounding=ROUND_HALF_UP
    )


def metric_tons_to_kg(tons: Decimal) -> Decimal:
    """Convert metric tons to kilograms."""
    return (tons * Decimal("1000")).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def cubic_meters_to_kg_natural_gas(m3: Decimal) -> Decimal:
    """
    Convert cubic meters of natural gas to kg.
    Standard density of natural gas ≈ 0.717 kg/m³ at STP.
    """
    return (m3 * Decimal("0.717")).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------------------
# Airport coordinates for distance calculation
# Covers major Indian domestic + key international airports
# ---------------------------------------------------------------------------
AIRPORT_COORDS = {
    # Indian domestic
    "BOM": (19.0896, 72.8656),    # Mumbai
    "DEL": (28.5562, 77.1000),    # Delhi
    "BLR": (13.1986, 77.7066),    # Bangalore
    "MAA": (12.9941, 80.1709),    # Chennai
    "CCU": (22.6547, 88.4467),    # Kolkata
    "HYD": (17.2403, 78.4294),    # Hyderabad
    "COK": (10.1520, 76.4019),    # Kochi
    "PNQ": (18.5822, 73.9197),    # Pune
    "GOI": (15.3808, 73.8314),    # Goa
    "AMD": (23.0772, 72.6347),    # Ahmedabad
    "JAI": (26.8242, 75.8122),    # Jaipur
    "IXC": (30.6735, 76.7885),    # Chandigarh
    "PAT": (25.5913, 85.0880),    # Patna
    "GAU": (26.1061, 91.5859),    # Guwahati
    "IXR": (23.3142, 85.3217),    # Ranchi
    "BBI": (20.2444, 85.8178),    # Bhubaneswar
    "LKO": (26.7606, 80.8893),    # Lucknow
    "VNS": (25.4524, 82.8593),    # Varanasi
    "TRV": (8.4821, 76.9199),     # Trivandrum
    "NAG": (21.0922, 79.0472),    # Nagpur
    # International
    "LHR": (51.4700, -0.4543),    # London Heathrow
    "DXB": (25.2532, 55.3657),    # Dubai
    "SIN": (1.3644, 103.9915),    # Singapore
    "JFK": (40.6413, -73.7781),   # New York JFK
    "SFO": (37.6213, -122.3790),  # San Francisco
    "FRA": (50.0333, 8.5706),     # Frankfurt
    "HKG": (22.3080, 113.9185),   # Hong Kong
    "NRT": (35.7720, 140.3929),   # Tokyo Narita
    "SYD": (-33.9399, 151.1753),  # Sydney
    "DOH": (25.2731, 51.6081),    # Doha
    "BKK": (13.6900, 100.7501),   # Bangkok
    "KUL": (2.7456, 101.7099),    # Kuala Lumpur
}


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> Decimal:
    """
    Calculate great-circle distance between two points using the Haversine formula.
    Returns distance in kilometers.
    """
    R = 6371.0  # Earth's radius in km

    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return Decimal(str(round(R * c, 1)))


def airport_distance_km(origin: str, destination: str) -> Decimal | None:
    """
    Calculate distance in km between two airports by IATA code.
    Returns None if either airport is unknown.
    """
    origin = origin.upper().strip()
    destination = destination.upper().strip()

    if origin not in AIRPORT_COORDS or destination not in AIRPORT_COORDS:
        return None

    lat1, lon1 = AIRPORT_COORDS[origin]
    lat2, lon2 = AIRPORT_COORDS[destination]

    return haversine_km(lat1, lon1, lat2, lon2)


def normalize_unit(quantity: Decimal, unit: str, fuel_type: str = "") -> tuple[Decimal, str]:
    """
    Normalize a quantity+unit pair to a standard unit.

    Returns (normalized_quantity, normalized_unit).
    Falls through to identity if unit is already standard or unknown.
    """
    unit_upper = unit.upper().strip()

    # SAP-style units
    if unit_upper in ("L", "LTR", "LITER", "LITERS"):
        return quantity, "liters"
    elif unit_upper in ("GAL", "GALLON", "GALLONS"):
        return gallons_to_liters(quantity), "liters"
    elif unit_upper in ("TO", "T", "MT", "METRIC_TON", "METRIC_TONS"):
        return metric_tons_to_kg(quantity), "kg"
    elif unit_upper in ("KG", "KGS"):
        return quantity, "kg"
    elif unit_upper in ("M3", "CBM", "CUBIC_METER"):
        if "gas" in fuel_type.lower():
            return cubic_meters_to_kg_natural_gas(quantity), "kg"
        return quantity, "m3"
    elif unit_upper in ("KWH",):
        return quantity, "kWh"
    elif unit_upper in ("KW",):
        return quantity, "kW"
    elif unit_upper in ("KM",):
        return quantity, "km"
    else:
        # Unknown unit — pass through with a note
        return quantity, unit
