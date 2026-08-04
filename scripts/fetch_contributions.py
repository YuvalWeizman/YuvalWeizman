#!/usr/bin/env python3
"""Scrape a GitHub user's public contribution calendar into JSON.

Uses the public (unauthenticated) HTML fragment GitHub serves at
/users/<username>/contributions -- no API token needed.
"""
import json
import os
import sys
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME", "YuvalWeizman")
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "contributions.json")


def fetch_days(username: str) -> list[dict]:
    url = f"https://github.com/users/{username}/contributions"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    days = []
    for td in soup.select("td.ContributionCalendar-day[data-date]"):
        date_str = td["data-date"]
        level = int(td.get("data-level", 0))
        days.append({"date": date_str, "level": level})

    if not days:
        raise RuntimeError("No contribution cells found -- GitHub markup may have changed")

    days.sort(key=lambda d: d["date"])
    return days


def to_grid(days: list[dict]) -> dict:
    """Assign each day a (week, weekday) cell matching GitHub's Sun-Sat columns."""
    dates = [datetime.strptime(d["date"], "%Y-%m-%d").date() for d in days]
    min_date = min(dates)
    # Origin = the Sunday on or before the earliest date.
    origin = min_date - timedelta(days=(min_date.weekday() + 1) % 7)

    cells = []
    max_week = 0
    for d, day in zip(dates, days):
        weekday = (d.weekday() + 1) % 7  # Sunday=0 .. Saturday=6
        week = (d - origin).days // 7
        max_week = max(max_week, week)
        cells.append({"date": day["date"], "level": day["level"], "week": week, "weekday": weekday})

    return {"weeks": max_week + 1, "cells": cells}


def main():
    days = fetch_days(GITHUB_USERNAME)
    grid = to_grid(days)
    grid["username"] = GITHUB_USERNAME
    grid["generated_at"] = datetime.utcnow().isoformat() + "Z"

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(grid, f, indent=2)

    print(f"Wrote {len(grid['cells'])} days across {grid['weeks']} weeks to {OUT_PATH}")


if __name__ == "__main__":
    main()
