# Holiday Planner: idea brief

The original need, as the owner gave it. `knowledge/spec/spec.json` cites this file as `SRC-001`.

- **Working name:** Holiday Planner.
- **User and concrete situation:** a family or a group of friends preparing a trip of one to a few
  weeks, sharing one laptop or a home network.
- **Observed problem:** the plan lives in chat threads, a spreadsheet for money and screenshots of
  bookings; activities collide, nobody knows who owes whom, and sharing the plan means sharing everything.
- **Desired observable outcome:** one local place for the trip: days, activities, money, packing,
  bookings, and a link that shows the plan to others without exposing the rest.
- **Two examples of success:** a 10-day trip to Lisbon with 4 travelers is planned day by day with no
  overlapping activities; after the trip, the balances settle to the cent.
- **One example of correct refusal:** adding a 09:30 museum visit to a day that already holds 09:00-10:00
  is refused, and the day is unchanged.
- **First scope:** the 20 features of `docs/feature-catalog.json`, served locally by Python's standard
  library with SQLite.
- **Explicit exclusions:** accounts and logins, payments, currency conversion, calls to external APIs,
  hosting, mobile apps.
- **Data, external systems and actors:** organizer, companions, guests with a link; a calendar
  application imports an .ics file; maps open from links.
- **Most costly plausible failure:** a share link exposing a family's whereabouts, or a split that loses
  money between friends.
- **Business decision owner:** the product owner (ACTOR-001).
- **Known facts:** one currency per trip; activities are planned in the destination's local time.
- **Proposals:** a 60-day limit per trip; the payer takes a split's remaining cents.
- **Unknowns that affect behavior or rights:** whether a completed trip becomes read-only (DEC-006).
