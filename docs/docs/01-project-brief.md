# Project brief: Electricity Usage Tracker (Topic 106)

## The idea in one sentence
**My app helps households to record their electricity meter readings, see how much they use each month, and estimate their bill.**

## The problem it solves
People do not know how much electricity they use until the bill arrives. This app lets them type in the number on their meter, then it works out the usage and the cost for them.

## Who uses it
One type of user: a **household**. Each household has an account and one or more meters. A household can only see its own data.

## What the user can do (5 user stories)
1. Sign up and log in, so my data is private.
2. Add my meter, so I can track it.
3. Enter a reading with a date (today or a past day), so the app knows my usage.
4. Get a clear message if I type a reading lower than the last one, so I can fix my mistake.
5. See my monthly usage in a chart with a bill estimate, so I can control my spending.

## What is in the project and what is not
| Included | Left for later or not included |
|---|---|
| Login, meters, readings, rules, monthly usage chart, bill estimate, sorting and paging | Payments (not needed for this project) |
| Edit and delete meters and readings | A daily chart (daily readings can be entered and are listed in the table) |
| Tests and a security check | Deployment on Vercel (planned for after everything works on the computer) |

## The three screens
```
 LOGIN                      DASHBOARD                           METER DETAIL
+----------------+      +-------------------------------+    +---------------------------------+
| Email  [____]  |      | Usage for [All my meters v]   |    | Home (No. 0412-5567-001)        |
| Pass   [____]  |      |   ▇   ▇▇  ▇▇▇  ▇▇  ▇▇▇        |    | Reading [____] Date [____] [Add]|
| [ Log in ]     |      |  Jun Jul Aug Sep Oct          |    | (red message if reading too low)|
| Create account |      | Bill estimate for the month   |    | Date   Reading  Used   [Delete] |
+----------------+      +-------------------------------+    +---------------------------------+
```
Other pages: My meters (list), Add meter (form), Bill estimator (type kWh, see the cost).

## Where each screen is in the code
Login: `client/app/login` · Dashboard: `client/app/page.js` · Meters and detail: `client/app/meters/` · Estimator: `client/app/estimate/`.
