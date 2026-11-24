-- =====================================================================
-- Sample data: 2 meters + 8 readings = 10 rows (tariff bands are in schema.sql)
-- 1) Sign up once in the web app (or Authentication -> Users -> Add user).
-- 2) Run this file. It attaches the samples to the FIRST user in auth.users.
-- Readings are taken at the end of each month (cumulative kWh on the meter).
-- =====================================================================

with owner as (select id from auth.users order by created_at limit 1),
m as (
  insert into meters (household_id, name, meter_number, location)
  select id, 'Home', '0412-5567-001', 'Kimironko, Kigali' from owner
  union all
  select id, 'Shop', '0412-5567-002', 'Remera, Kigali' from owner
  returning id, name
)
insert into readings (meter_id, kwh, read_date)
select m.id, r.kwh, r.read_date
from m
join (values
  ('Home', 1200.00, date '2026-05-31'),
  ('Home', 1245.50, date '2026-06-30'),
  ('Home', 1298.00, date '2026-07-31'),
  ('Home', 1362.25, date '2026-08-31'),
  ('Home', 1410.00, date '2026-09-30'),
  ('Home', 1478.75, date '2026-10-31'),
  ('Shop',  300.00, date '2026-09-30'),
  ('Shop',  392.50, date '2026-10-31')
) as r(meter, kwh, read_date) on r.meter = m.name;
