# DeskBook - Product Requirements (v0.3, draft)

Owner: Facilities & HR. Demo PRD for the product factory walkthrough.

## 1. Background
Since hybrid work started, our offices are half empty on Mondays and Fridays and overfull mid-week.
Employees arrive and find no desk. Facilities has no data on real usage, so we keep paying for floors nobody
uses. We want a simple app where employees book a desk before they come in.

## 2. Goals
- Employees always find a desk when they come in.
- Facilities sees real usage per office and floor to plan space.
- Managers can see who of their team is in the office on a given day, so teams can meet in person.
- The app should be fast and easy to use.

## 3. Users
- Employee - books and cancels desks.
- Manager - sees team attendance, can book for their team.
- Facilities admin - sets up offices, floors and desks, sees reports.

## 4. Features
### 4.1 Office setup
Admins create offices (name, city, timezone), floors and desks. Each desk has a code (e.g. "BLR-3-14"),
and can have features such as a monitor, docking station or standing desk. Admins can block a desk for
maintenance.

### 4.2 Booking
- An employee picks an office, a date and a desk on a list or floor map, and books it.
- Bookings are for a full day, or half day (morning/afternoon).
- An employee can book up to 2 weeks ahead.
- One booking per employee per day.
- Employees can cancel a booking any time.
- Recurring bookings (e.g. every Tuesday) should be possible.

### 4.3 Check-in
Employees check in when they arrive (button in the app, or QR code on the desk). If they do not check in by
10:00, the booking is released so someone else can take the desk.

### 4.4 Team view
Managers see a week calendar of who in their team has booked which day and where. Managers can book desks
for their team members, and can book a group of desks near each other for a team day.

### 4.5 Reports
Facilities sees occupancy per office, floor and day (booked vs checked-in vs capacity), no-show rate, and the
busiest days. Export to Excel.

### 4.6 Notifications
Reminder the evening before, and a message when a booking is released. Etc.

## 5. Non-functional
- Real time availability.
- Works on mobile.
- Must integrate with SuccessFactors for employees and managers.
- About 3,000 employees in 4 offices now, more offices next year.
- English first; German and French later.

## 6. Out of scope
Meeting room booking (maybe phase 2). Parking.

## 7. Open
- TBD: what happens with no-shows repeatedly?
