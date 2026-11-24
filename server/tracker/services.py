"""Business logic that is shared by several endpoints."""
from collections import defaultdict
from decimal import Decimal

from .models import Reading


def monthly_consumption(meter_ids):
    """
    Consumption of a reading = its kWh minus the previous reading's kWh (same meter),
    counted in the month of the reading's date. The first reading of a meter is a baseline.
    Returns {(meter_id, 'YYYY-MM'): Decimal}.
    """
    totals = defaultdict(Decimal)
    previous = {}
    qs = Reading.objects.filter(meter_id__in=meter_ids).order_by("meter_id", "read_date")
    for r in qs:
        prev = previous.get(r.meter_id)
        if prev is not None:
            totals[(r.meter_id, r.read_date.strftime("%Y-%m"))] += r.kwh - prev
        previous[r.meter_id] = r.kwh
    return totals
