import uuid
from datetime import date, timedelta
from unittest.mock import patch

from django.core.cache import cache
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APITestCase

from .models import Meter, Profile, Reading, TariffBand

ALICE, BOB, VISITOR = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
USERS = {
    "alice-token": {"id": ALICE, "email": "alice@example.com"},
    "bob-token": {"id": BOB, "email": "bob@example.com"},
    "visitor-token": {"id": VISITOR, "email": "v@example.com"},
}


def fake_supabase(token):
    if token in USERS:
        return USERS[token]
    raise AuthenticationFailed("Invalid or expired login token. Please log in again.")


class ApiTestCase(APITestCase):
    """Replaces the real call to Supabase Auth, so tests need no internet."""

    def setUp(self):
        cache.clear()
        patcher = patch("tracker.authentication.fetch_supabase_user", side_effect=fake_supabase)
        patcher.start()
        self.addCleanup(patcher.stop)
        TariffBand.objects.create(name="B1", from_kwh=0, to_kwh=20, rate_rwf=89)
        TariffBand.objects.create(name="B2", from_kwh=20, to_kwh=50, rate_rwf=310)
        TariffBand.objects.create(name="B3", from_kwh=50, to_kwh=None, rate_rwf=369)
        Profile.objects.create(id=VISITOR, role="visitor")
        self.meter = Meter.objects.create(household_id=ALICE, name="Home", meter_number="M-1")
        self.login("alice-token")

    def login(self, token):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def add(self, kwh, day, meter=None):
        return Reading.objects.create(meter=meter or self.meter, kwh=kwh, read_date=day)

    @property
    def readings_url(self):
        return f"/api/meters/{self.meter.id}/readings/"


class AuthTests(ApiTestCase):
    def test_no_token_is_401(self):
        self.client.credentials()
        self.assertEqual(self.client.get("/api/meters/").status_code, 401)

    def test_bad_token_is_401(self):
        self.login("nonsense")
        r = self.client.get("/api/meters/")
        self.assertEqual(r.status_code, 401)
        self.assertIn("error", r.json())

    def test_wrong_role_is_403(self):
        self.login("visitor-token")
        self.assertEqual(self.client.get("/api/meters/").status_code, 403)

    def test_me_returns_role(self):
        r = self.client.get("/api/me/")
        self.assertEqual((r.status_code, r.json()["role"]), (200, "household"))


class MeterTests(ApiTestCase):
    def test_create_list_update_delete(self):
        r = self.client.post("/api/meters/", {"name": "Shop", "meter_number": "M-2"}, format="json")
        self.assertEqual(r.status_code, 201)
        mid = r.json()["id"]
        self.assertEqual(self.client.get("/api/meters/").json()["count"], 2)
        self.assertEqual(self.client.patch(f"/api/meters/{mid}/", {"name": "Store"}, format="json").status_code, 200)
        self.assertEqual(self.client.delete(f"/api/meters/{mid}/").status_code, 204)
        self.assertEqual(self.client.get(f"/api/meters/{mid}/").status_code, 404)

    def test_bad_input_is_400(self):
        self.assertEqual(self.client.post("/api/meters/", {"name": "  ", "meter_number": "X"}, format="json").status_code, 400)
        self.assertEqual(self.client.post("/api/meters/", {"name": "A"}, format="json").status_code, 400)
        dup = self.client.post("/api/meters/", {"name": "A", "meter_number": "M-1"}, format="json")
        self.assertEqual(dup.status_code, 400)

    def test_too_long_values_are_400(self):
        body = {"name": "x" * 101, "meter_number": "OK-1"}
        r = self.client.post("/api/meters/", body, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("100", r.json()["error"])
        long_loc = {"name": "A", "meter_number": "OK-2", "location": "y" * 201}
        self.assertEqual(self.client.post("/api/meters/", long_loc, format="json").status_code, 400)

    def test_huge_reading_is_400(self):
        r = self.client.post(self.readings_url, {"kwh": 10**12, "read_date": "2026-10-01"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_script_text_is_stored_as_plain_text(self):
        # The server keeps it as ordinary text; React then shows it as text, never runs it.
        evil = "<script>alert(1)</script>"
        r = self.client.post("/api/meters/", {"name": evil, "meter_number": "XSS-1"}, format="json")
        self.assertEqual((r.status_code, r.json()["name"]), (201, evil))

    def test_missing_meter_is_404(self):
        self.assertEqual(self.client.get("/api/meters/9999/").status_code, 404)

    def test_other_household_cannot_see_my_meter(self):
        self.login("bob-token")
        self.assertEqual(self.client.get(f"/api/meters/{self.meter.id}/").status_code, 404)
        self.assertEqual(self.client.get("/api/meters/").json()["count"], 0)


class ReadingRuleTests(ApiTestCase):
    def test_valid_reading_is_201_with_consumption(self):
        self.add(1000, date(2026, 9, 30))
        r = self.client.post(self.readings_url, {"kwh": 1060.5, "read_date": "2026-10-31"}, format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["consumption_kwh"], 60.5)

    def test_lower_reading_is_400_with_clear_message(self):          # the Break-it challenge
        self.add(1000, date(2026, 9, 30))
        r = self.client.post(self.readings_url, {"kwh": 900, "read_date": "2026-10-31"}, format="json")
        self.assertEqual(r.status_code, 400)
        self.assertIn("cannot be lower than the previous one", r.json()["error"])
        self.assertEqual(Reading.objects.count(), 1)                 # nothing was saved

    def test_equal_reading_is_allowed(self):
        self.add(1000, date(2026, 9, 30))
        r = self.client.post(self.readings_url, {"kwh": 1000, "read_date": "2026-10-31"}, format="json")
        self.assertEqual(r.status_code, 201)

    def test_backdated_reading_higher_than_later_one_is_400(self):
        self.add(1000, date(2026, 8, 31))
        self.add(1100, date(2026, 10, 31))
        r = self.client.post(self.readings_url, {"kwh": 1200, "read_date": "2026-09-30"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_other_bad_input_is_400(self):
        cases = [
            {"kwh": -5, "read_date": "2026-10-01"},                       # negative
            {"kwh": "abc", "read_date": "2026-10-01"},                    # not a number
            {"kwh": 10, "read_date": "31/10/2026"},                       # wrong date format
            {"kwh": 10, "read_date": (date.today() + timedelta(days=3)).isoformat()},  # future
            {"read_date": "2026-10-01"},                                  # missing kwh
        ]
        for body in cases:
            with self.subTest(body=body):
                self.assertEqual(self.client.post(self.readings_url, body, format="json").status_code, 400)

    def test_duplicate_date_is_400(self):
        self.add(1000, date(2026, 9, 30))
        r = self.client.post(self.readings_url, {"kwh": 1010, "read_date": "2026-09-30"}, format="json")
        self.assertEqual(r.status_code, 400)

    def test_reading_on_missing_or_foreign_meter_is_404(self):
        body = {"kwh": 1, "read_date": "2026-10-01"}
        self.assertEqual(self.client.post("/api/meters/9999/readings/", body, format="json").status_code, 404)
        self.login("bob-token")
        self.assertEqual(self.client.post(self.readings_url, body, format="json").status_code, 404)

    def test_patch_applies_same_rule_and_delete_works(self):
        a = self.add(1000, date(2026, 8, 31))
        b = self.add(1100, date(2026, 9, 30))
        bad = self.client.patch(f"/api/readings/{b.id}/", {"kwh": 900}, format="json")
        self.assertEqual(bad.status_code, 400)
        ok = self.client.patch(f"/api/readings/{b.id}/", {"kwh": 1150}, format="json")
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(self.client.delete(f"/api/readings/{a.id}/").status_code, 204)
        self.assertEqual(self.client.get(f"/api/readings/{a.id}/").status_code, 404)

    def test_pagination_and_sorting(self):
        for i in range(12):
            self.add(1000 + i * 10, date(2026, 1, 1) + timedelta(days=i))
        page1 = self.client.get(self.readings_url).json()
        self.assertEqual((page1["count"], len(page1["results"])), (12, 10))
        self.assertEqual(page1["results"][0]["read_date"], "2026-01-12")      # newest first by default
        asc = self.client.get(self.readings_url + "?ordering=kwh&page_size=3").json()
        self.assertEqual([r["kwh"] for r in asc["results"]], [1000, 1010, 1020])


class BillAndAnalyticsTests(ApiTestCase):
    def test_estimate_uses_tariff_bands(self):
        # 20*89 + 30*310 + 20*369 = 1780 + 9300 + 7380
        r = self.client.get("/api/bill/estimate/?kwh=70")
        self.assertEqual((r.status_code, r.json()["total_rwf"]), (200, 18460))
        self.assertEqual(len(r.json()["lines"]), 3)
        self.assertEqual(self.client.get("/api/bill/estimate/?kwh=10").json()["total_rwf"], 890)
        self.assertEqual(self.client.get("/api/bill/estimate/?kwh=0").json()["total_rwf"], 0)

    def test_estimate_bad_input_is_400(self):
        for q in ["", "?kwh=abc", "?kwh=-4"]:
            with self.subTest(q=q):
                self.assertEqual(self.client.get("/api/bill/estimate/" + q).status_code, 400)

    def test_monthly_analytics_and_meter_bill(self):
        self.add(1000, date(2026, 8, 31))
        self.add(1040, date(2026, 9, 30))    
        self.add(1110, date(2026, 10, 31))    
        data = self.client.get(f"/api/analytics/monthly/?meter={self.meter.id}").json()
        self.assertEqual([(m["month"], m["kwh"]) for m in data["months"]], [("2026-09", 40.0), ("2026-10", 70.0)])
        self.assertEqual(data["months"][1]["bill_rwf"], 18460)
        bill = self.client.get(f"/api/meters/{self.meter.id}/bill/?month=2026-10").json()
        self.assertEqual(bill["total_rwf"], 18460)
        latest = self.client.get(f"/api/meters/{self.meter.id}/bill/").json()
        self.assertEqual(latest["month"], "2026-10")

    def test_bill_errors(self):
        self.add(1000, date(2026, 8, 31))
        url = f"/api/meters/{self.meter.id}/bill/"
        self.assertEqual(self.client.get(url).status_code, 404)                   # no consumption yet
        self.assertEqual(self.client.get(url + "?month=oct").status_code, 400)    # bad format
        self.assertEqual(self.client.get("/api/meters/9999/bill/").status_code, 404)

    def test_analytics_only_counts_my_meters(self):
        other = Meter.objects.create(household_id=BOB, name="B", meter_number="M-B")
        self.add(500, date(2026, 9, 30), other)
        self.add(900, date(2026, 10, 31), other)
        self.assertEqual(self.client.get("/api/analytics/monthly/").json()["months"], [])
        self.assertEqual(self.client.get(f"/api/analytics/monthly/?meter={other.id}").status_code, 404)
