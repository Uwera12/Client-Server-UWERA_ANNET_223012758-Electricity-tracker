from django.db.models import OuterRef, Subquery
from django.utils import timezone
from rest_framework import serializers

from .models import Meter, Reading, TariffBand

_MISSING = object()


class MeterSerializer(serializers.ModelSerializer):
    latest_kwh = serializers.SerializerMethodField()
    latest_read_date = serializers.SerializerMethodField()

    class Meta:
        model = Meter
        fields = ["id", "name", "meter_number", "location", "created_at", "latest_kwh", "latest_read_date"]
        read_only_fields = ["id", "created_at"]
        # Length limits: never accept huge values (also enforced in the database).
        extra_kwargs = {
            "name": {"max_length": 100},
            "meter_number": {"max_length": 50},
            "location": {"max_length": 200},
        }

    def _latest(self, obj):
        readings = list(obj.readings.all())          # prefetched by the view
        return max(readings, key=lambda r: r.read_date) if readings else None

    def get_latest_kwh(self, obj):
        r = self._latest(obj)
        return float(r.kwh) if r else None

    def get_latest_read_date(self, obj):
        r = self._latest(obj)
        return r.read_date.isoformat() if r else None

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Name cannot be blank.")
        return value.strip()

    def validate_meter_number(self, value):
        if not value.strip():
            raise serializers.ValidationError("Meter number cannot be blank.")
        return value.strip()


class ReadingSerializer(serializers.ModelSerializer):
    kwh = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0, coerce_to_string=False)
    consumption_kwh = serializers.SerializerMethodField()

    class Meta:
        model = Reading
        fields = ["id", "meter", "kwh", "read_date", "consumption_kwh", "created_at"]
        read_only_fields = ["id", "meter", "created_at"]

    def get_consumption_kwh(self, obj):
        prev = getattr(obj, "prev_kwh", _MISSING)
        if prev is _MISSING:
            row = (Reading.objects.filter(meter=obj.meter, read_date__lt=obj.read_date)
                   .order_by("-read_date").first())
            prev = row.kwh if row else None
        return None if prev is None else float(obj.kwh - prev)

    def validate(self, attrs):
        """THE BUSINESS RULE (server side): readings only ever go up as dates go forward."""
        instance = self.instance
        meter = instance.meter if instance else self.context["meter"]
        kwh = attrs.get("kwh", instance.kwh if instance else None)
        read_date = attrs.get("read_date", instance.read_date if instance else None)

        others = Reading.objects.filter(meter=meter)
        if instance:
            others = others.exclude(pk=instance.pk)

        if read_date > timezone.localdate():
            raise serializers.ValidationError({"read_date": "The reading date cannot be in the future."})
        if others.filter(read_date=read_date).exists():
            raise serializers.ValidationError(
                {"read_date": f"This meter already has a reading for {read_date}. Edit that one instead."})

        previous = others.filter(read_date__lt=read_date).order_by("-read_date").first()
        if previous and kwh < previous.kwh:
            raise serializers.ValidationError({"kwh": (
                f"A new reading cannot be lower than the previous one. You entered {kwh:.2f} kWh, "
                f"but the reading on {previous.read_date} was {previous.kwh:.2f} kWh.")})

        following = others.filter(read_date__gt=read_date).order_by("read_date").first()
        if following and kwh > following.kwh:
            raise serializers.ValidationError({"kwh": (
                f"This reading is higher than the later reading on {following.read_date} "
                f"({following.kwh:.2f} kWh). Readings must never go down over time.")})
        return attrs


def with_previous_kwh(queryset):
    """Annotate each reading with the previous reading's kWh (same meter) in one SQL query."""
    prev = (Reading.objects.filter(meter=OuterRef("meter"), read_date__lt=OuterRef("read_date"))
            .order_by("-read_date").values("kwh")[:1])
    return queryset.annotate(prev_kwh=Subquery(prev))


class TariffBandSerializer(serializers.ModelSerializer):
    class Meta:
        model = TariffBand
        fields = ["id", "name", "from_kwh", "to_kwh", "rate_rwf"]
