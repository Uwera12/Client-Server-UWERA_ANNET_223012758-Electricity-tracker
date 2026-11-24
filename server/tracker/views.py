import logging
import re
from decimal import Decimal, InvalidOperation

from rest_framework import generics, status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .billing import calculate_bill, get_bands
from .models import Meter, Reading, TariffBand
from .serializers import (MeterSerializer, ReadingSerializer, TariffBandSerializer,
                          with_previous_kwh)
from .services import monthly_consumption

log = logging.getLogger("tracker")
MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def my_meters(request):
    """Every query starts here: a household only ever sees ITS OWN meters."""
    return Meter.objects.filter(household_id=request.user.id)


def get_my_meter(request, meter_id):
    try:
        return my_meters(request).get(pk=meter_id)
    except Meter.DoesNotExist:
        raise NotFound(f"Meter {meter_id} not found.")


# ------------------------------------------------------------------ misc
class HealthView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "ok"})


class MeView(APIView):
    def get(self, request):
        u = request.user
        return Response({"id": u.id, "email": u.email, "role": u.role})


class TariffList(generics.ListAPIView):
    queryset = TariffBand.objects.order_by("from_kwh")
    serializer_class = TariffBandSerializer
    pagination_class = None


class BillEstimate(APIView):
    """GET /api/bill/estimate/?kwh=120  ->  what would 120 kWh cost under the tariff bands?"""

    def get(self, request):
        raw = request.query_params.get("kwh")
        if raw is None:
            raise ValidationError({"kwh": "Query parameter 'kwh' is required, e.g. ?kwh=120"})
        try:
            kwh = Decimal(raw)
        except InvalidOperation:
            raise ValidationError({"kwh": "'kwh' must be a number."})
        if kwh < 0 or kwh > 1_000_000:
            raise ValidationError({"kwh": "'kwh' must be between 0 and 1,000,000."})
        return Response(calculate_bill(kwh))


# ------------------------------------------------------------------ meters
class MeterList(generics.ListCreateAPIView):
    serializer_class = MeterSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        return my_meters(self.request).prefetch_related("readings")

    def perform_create(self, serializer):
        meter = serializer.save(household_id=self.request.user.id)
        log.info("Meter created: id=%s number=%s", meter.id, meter.meter_number)


class MeterDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MeterSerializer
    http_method_names = ["get", "patch", "delete", "options"]

    def get_object(self):
        return get_my_meter(self.request, self.kwargs["pk"])

    def perform_destroy(self, instance):
        log.info("Meter deleted: id=%s (its readings are deleted too)", instance.id)
        instance.delete()


# ------------------------------------------------------------------ readings
class ReadingList(generics.ListCreateAPIView):
    serializer_class = ReadingSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ["read_date", "kwh"]
    ordering = ["-read_date"]

    def get_queryset(self):
        meter = get_my_meter(self.request, self.kwargs["meter_id"])
        return with_previous_kwh(Reading.objects.filter(meter=meter).select_related("meter"))

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        if self.request.method == "POST":
            ctx["meter"] = get_my_meter(self.request, self.kwargs["meter_id"])
        return ctx

    def perform_create(self, serializer):
        reading = serializer.save(meter=serializer.context["meter"])
        log.info("Reading accepted: meter=%s kwh=%s date=%s", reading.meter_id, reading.kwh, reading.read_date)


class ReadingDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ReadingSerializer
    http_method_names = ["get", "patch", "delete", "options"]

    def get_object(self):
        try:
            return (Reading.objects.select_related("meter")
                    .get(pk=self.kwargs["pk"], meter__household_id=self.request.user.id))
        except Reading.DoesNotExist:
            raise NotFound(f"Reading {self.kwargs['pk']} not found.")

    def perform_update(self, serializer):
        r = serializer.save()
        log.info("Reading updated: id=%s kwh=%s date=%s", r.id, r.kwh, r.read_date)

    def perform_destroy(self, instance):
        log.info("Reading deleted: id=%s", instance.id)
        instance.delete()


# ------------------------------------------------------------------ bills & analytics
class MeterBill(APIView):
    """GET /api/meters/<id>/bill/?month=2026-10  (month optional: defaults to the latest)."""

    def get(self, request, meter_id):
        meter = get_my_meter(request, meter_id)
        totals = {m: v for (mid, m), v in monthly_consumption([meter.id]).items()}
        month = request.query_params.get("month")
        if month is not None and not MONTH_RE.match(month):
            raise ValidationError({"month": "Use the format YYYY-MM, for example 2026-10."})
        if month is None:
            if not totals:
                raise NotFound("No consumption yet. Add at least two readings for this meter.")
            month = max(totals)
        if month not in totals:
            raise NotFound(f"No consumption recorded for {month}.")
        bill = calculate_bill(totals[month])
        return Response({"meter": meter.id, "month": month, **bill})


class MonthlyAnalytics(APIView):
    """GET /api/analytics/monthly/?meter=<id>  -> kWh and bill per month (all my meters if omitted)."""

    def get(self, request):
        raw = request.query_params.get("meter")
        if raw is not None:
            if not raw.isdigit():
                raise ValidationError({"meter": "'meter' must be a meter id (a whole number)."})
            ids = [get_my_meter(request, int(raw)).id]
        else:
            ids = list(my_meters(request).values_list("id", flat=True))

        bands = get_bands()
        months = {}
        for (mid, month), kwh in monthly_consumption(ids).items():
            row = months.setdefault(month, {"month": month, "kwh": Decimal("0"), "bill_rwf": 0})
            row["kwh"] += kwh
            row["bill_rwf"] += calculate_bill(kwh, bands)["total_rwf"]   # each meter has its own bill
        data = [{"month": m, "kwh": float(r["kwh"]), "bill_rwf": r["bill_rwf"]}
                for m, r in sorted(months.items())]
        return Response({"meter": int(raw) if raw else None, "months": data})
