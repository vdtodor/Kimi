# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains three independent Python implementations of a flight routing system. All three scripts solve the same problem — parsing a flight schedule and producing direct/indirect flight listings — using different data structures and algorithms. The code and variable names are written in Serbian.

## Running the Scripts

Each file is a standalone script with no external dependencies (standard library only: `sys`, `os`, `bisect`).

```bash
python CC_Flights.py
python G_flights.py
python OAI_flights.py
```

**Required input at runtime:**
- **stdin**: a city pair in the format `CITY1->CITY2`
- **`flights.txt`** in the working directory: the flight schedule data

**Output files produced:**
- `flights_direct.txt` — direct flight results
- `flights_indirect.txt` — indirect (connecting) flight results

**Flight schedule format** (`flights.txt`):
```
airline|departure->arrival|HH:MM-HH:MM,price;HH:MM-HH:MM,price;...
```

## Architecture

All three files follow the same two-phase pipeline:

1. **Parse** `flights.txt` into an in-memory structure grouped by city-pair route.
2. **Query** that structure for direct flights (routes matching the input pair) and indirect flights (routes via an intermediate city where the second leg departs after the first arrives).

**Output conventions:**
- Direct flights sorted: route lexicographically → airline lexicographically → departure time ascending.
- Indirect flights sorted: first departure time → total duration → airline name.
- Prices always formatted to 2 decimal places.

**Error handling:**
- `"DAT_GRESKA"` printed to stdout if `flights.txt` cannot be opened.
- `"GRESKA"` printed for any other exception.
- Silent exit if stdin input is empty.

## Differences Between the Three Implementations

| Aspect | CC_Flights.py | G_flights.py | OAI_flights.py |
|---|---|---|---|
| Data structure | List of dicts | `dict` keyed by `(city1, city2)` | `dict` keyed by `(city1, city2)` with tuples |
| Time storage | String only | String + integer | String + integer tuple |
| Connection search | O(n²) | O(n²) | O(n log n) via `bisect_left` |
| Direct flight output | One flight per line | One flight per line | Semicolon-separated per airline |
| Comments | Minimal | Extensive (Serbian) | Clear algorithmic notes |

`OAI_flights.py` is the most optimized implementation; `G_flights.py` is the most thoroughly commented.

## Key Serbian Terms in the Code

| Serbian | English |
|---|---|
| `letovi` | flights |
| `grad` | city |
| `ruta` | route |
| `aviokompanija` | airline |
| `vreme` | time |
| `cena` | price |
| `polazak` / `dolazak` | departure / arrival |
| `direktni` | direct |
| `indirektni` | indirect |
| `greska` | error |
