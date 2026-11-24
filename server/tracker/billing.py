"""Tariff-band billing: each slice of consumption is charged at its own band's rate."""
from decimal import Decimal, ROUND_HALF_UP

from .models import TariffBand


def get_bands():
    return list(TariffBand.objects.order_by("from_kwh"))


def calculate_bill(kwh, bands=None):
    """Return {'consumption_kwh', 'lines': [...], 'total_rwf'} for `kwh` kilowatt-hours."""
    kwh = Decimal(str(kwh))
    bands = get_bands() if bands is None else bands
    lines, total = [], Decimal("0")
    for band in bands:
        if kwh <= band.from_kwh:
            break
        upper = band.to_kwh if band.to_kwh is not None else kwh
        used = min(kwh, upper) - band.from_kwh
        charge = used * band.rate_rwf
        total += charge
        lines.append({
            "band": band.name,
            "from_kwh": float(band.from_kwh),
            "to_kwh": float(band.to_kwh) if band.to_kwh is not None else None,
            "kwh": float(used),
            "rate_rwf": float(band.rate_rwf),
            "charge_rwf": int(charge.quantize(Decimal("1"), rounding=ROUND_HALF_UP)),
        })
    return {
        "consumption_kwh": float(kwh),
        "lines": lines,
        "total_rwf": int(total.quantize(Decimal("1"), rounding=ROUND_HALF_UP)),
        "currency": "RWF",
    }
