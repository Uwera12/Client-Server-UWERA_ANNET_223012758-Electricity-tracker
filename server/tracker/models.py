"""
These models MIRROR the tables created in supabase/schema.sql.
managed = False means Django never creates or alters them: Supabase owns the schema.
"""
from django.db import models


class Profile(models.Model):
    id = models.UUIDField(primary_key=True)
    full_name = models.TextField(null=True, blank=True)
    role = models.TextField(default="household")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "profiles"


class Meter(models.Model):
    household_id = models.UUIDField()            # = Supabase Auth user id
    name = models.TextField()
    meter_number = models.TextField(unique=True)
    location = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "meters"


class Reading(models.Model):
    meter = models.ForeignKey(Meter, on_delete=models.CASCADE, related_name="readings", db_column="meter_id")
    kwh = models.DecimalField(max_digits=10, decimal_places=2)   # cumulative value on the meter
    read_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "readings"


class TariffBand(models.Model):
    name = models.TextField()
    from_kwh = models.DecimalField(max_digits=10, decimal_places=2)
    to_kwh = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # NULL = no limit
    rate_rwf = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = "tariff_bands"
