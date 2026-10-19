# Job Application Tracker

A free, offline desktop app for Windows that keeps track of your job applications.
It uses only built-in Python (Tkinter + SQLite), so there is nothing to buy and nothing extra to install.

## Features
- Add, edit and delete applications (company, role, status, dates, link, notes)
- Statuses: Wishlist → Applied → Interview → Offer / Rejected
- Search and filter by status
- Follow-up reminders: rows due for follow-up are highlighted, and a popup lists them on startup
- Counts per status at the bottom
- Export everything to CSV (opens in Excel)

## Run it on Windows
1. Install Python (free) from https://www.python.org/downloads/ and tick **"Add python.exe to PATH"** during setup.
2. Download this repo (green **Code** button → **Download ZIP**) and unzip it, or `git clone` it.
3. Double-click **`run.bat`**, or from a terminal in the folder run:
   ```
   python -m job_tracker.app
   ```

Your data is saved in `job_applications.db` in your user folder (e.g. `C:\Users\<you>\`).

## Run the tests
```
python -m unittest discover tests
```
