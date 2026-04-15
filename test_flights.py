"""
Tests for the three flight routing implementations:
CC_Flights.py, G_flights.py, OAI_flights.py.

Each script follows the same pipeline:
  1. Read a city pair from stdin (CITY1->CITY2)
  2. Parse flights.txt
  3. Write flights_direct.txt and flights_indirect.txt

Integration tests run the scripts via subprocess in a temp directory so
each test gets a clean file system state. Utility-function tests import
each module directly (the `if __name__ == "__main__"` guard prevents
main() from running at import time).
"""
import importlib.util
import os
import re
import subprocess
import sys
import tempfile
import textwrap

import pytest

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = ["CC_Flights.py", "G_flights.py", "OAI_flights.py"]

# ---------------------------------------------------------------------------
# Shared sample data
# ---------------------------------------------------------------------------
SAMPLE_FLIGHTS = textwrap.dedent("""\
    AirSrbia|Beograd->Pariz|08:00-10:00,150.00;12:00-14:00,180.00
    AirFrance|Beograd->Pariz|09:00-11:00,200.00
    AirSrbia|Beograd->Frankfurt|07:00-09:00,120.00
    Lufthansa|Frankfurt->Pariz|10:00-11:30,90.00
""")


# ---------------------------------------------------------------------------
# Helper: run one script in an isolated temp directory
# ---------------------------------------------------------------------------
def run_script(script_name, stdin_input, flights_content=SAMPLE_FLIGHTS):
    """Run script_name with stdin_input and a flights.txt in a fresh temp dir.

    Returns (CompletedProcess, direct_txt_content, indirect_txt_content).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "flights.txt"), "w", encoding="utf-8") as f:
            f.write(flights_content)

        result = subprocess.run(
            [sys.executable, os.path.join(REPO_DIR, script_name)],
            input=stdin_input,
            capture_output=True,
            text=True,
            cwd=tmpdir,
        )

        def read_out(name):
            p = os.path.join(tmpdir, name)
            return open(p, encoding="utf-8").read() if os.path.exists(p) else ""

        return result, read_out("flights_direct.txt"), read_out("flights_indirect.txt")


# ---------------------------------------------------------------------------
# Helper: load a module without triggering __main__
# ---------------------------------------------------------------------------
def load_module(filename):
    spec = importlib.util.spec_from_file_location(
        filename.replace(".py", ""), os.path.join(REPO_DIR, filename)
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ===========================================================================
# Utility-function unit tests
# ===========================================================================

class TestCCUtilities:
    @pytest.fixture(autouse=True)
    def _load(self):
        self.mod = load_module("CC_Flights.py")

    def test_vreme_u_minute(self):
        assert self.mod.vreme_u_minute("00:00") == 0
        assert self.mod.vreme_u_minute("01:00") == 60
        assert self.mod.vreme_u_minute("08:30") == 510

    def test_trajanje_leta(self):
        assert self.mod.trajanje_leta("08:00", "10:00") == 120
        assert self.mod.trajanje_leta("07:00", "09:30") == 150


class TestGUtilities:
    @pytest.fixture(autouse=True)
    def _load(self):
        self.mod = load_module("G_flights.py")

    def test_parsiraj_vreme(self):
        assert self.mod.parsiraj_vreme("00:00") == 0
        assert self.mod.parsiraj_vreme("08:30") == 510
        assert self.mod.parsiraj_vreme("23:59") == 23 * 60 + 59

    def test_parsiraj_vreme_invalid_hour(self):
        with pytest.raises(ValueError):
            self.mod.parsiraj_vreme("25:00")

    def test_parsiraj_vreme_no_colon(self):
        with pytest.raises((ValueError, Exception)):
            self.mod.parsiraj_vreme("0800")

    def test_formatiraj_cenu(self):
        assert self.mod.formatiraj_cenu(150.0) == "150.00"
        assert self.mod.formatiraj_cenu(9.5) == "9.50"
        assert self.mod.formatiraj_cenu(1000) == "1000.00"


class TestOAIUtilities:
    @pytest.fixture(autouse=True)
    def _load(self):
        self.mod = load_module("OAI_flights.py")

    def test_time_to_min(self):
        assert self.mod.time_to_min("00:00") == 0
        assert self.mod.time_to_min("08:00") == 480
        assert self.mod.time_to_min("12:30") == 750

    def test_flight_sort_key_orders_by_departure(self):
        # flight tuple: (airline, dep_city, lan_city, dep_min, lan_min, dep_str, lan_str, price)
        early = ("AirX", "A", "B", 480, 600, "08:00", "10:00", 100.0)
        late = ("AirX", "A", "B", 540, 660, "09:00", "11:00", 100.0)
        assert self.mod.flight_sort_key(early) < self.mod.flight_sort_key(late)


# ===========================================================================
# Integration tests: error handling
# ===========================================================================

@pytest.mark.parametrize("script", SCRIPTS)
def test_missing_flights_file_prints_dat_greska(script):
    """When flights.txt is absent every script must print DAT_GRESKA."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            [sys.executable, os.path.join(REPO_DIR, script)],
            input="Beograd->Pariz",
            capture_output=True,
            text=True,
            cwd=tmpdir,
        )
    assert "DAT_GRESKA" in result.stdout


@pytest.mark.parametrize("script", SCRIPTS)
def test_empty_stdin_exits_silently(script):
    """Empty stdin must produce no stdout and exit 0."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "flights.txt"), "w") as f:
            f.write(SAMPLE_FLIGHTS)
        result = subprocess.run(
            [sys.executable, os.path.join(REPO_DIR, script)],
            input="",
            capture_output=True,
            text=True,
            cwd=tmpdir,
        )
    assert result.stdout.strip() == ""
    assert result.returncode == 0


# ===========================================================================
# Integration tests: flights_direct.txt content
# ===========================================================================

@pytest.mark.parametrize("script", SCRIPTS)
def test_direct_output_contains_all_routes(script):
    """All three routes in SAMPLE_FLIGHTS must appear in flights_direct.txt."""
    _, direct, _ = run_script(script, "Beograd->Pariz")
    assert "Beograd->Pariz" in direct
    assert "Beograd->Frankfurt" in direct
    assert "Frankfurt->Pariz" in direct


@pytest.mark.parametrize("script", SCRIPTS)
def test_direct_output_price_always_two_decimals(script):
    """Every price token in flights_direct.txt must have exactly 2 decimal places."""
    _, direct, _ = run_script(script, "Beograd->Pariz")
    prices = re.findall(r'\d+\.\d+', direct)
    assert prices, "No prices found in direct output"
    for price in prices:
        assert len(price.split('.')[1]) == 2, f"Bad price format: {price}"


@pytest.mark.parametrize("script", SCRIPTS)
def test_direct_output_airlines_alphabetical(script):
    """Airlines on the Beograd->Pariz route must appear in lexicographic order.

    AirFrance < AirSrbia alphabetically, so AirFrance must occur first
    regardless of which output format the script uses.
    """
    _, direct, _ = run_script(script, "Beograd->Pariz")
    # Search only within the Beograd->Pariz block so that AirSrbia entries
    # on earlier routes (e.g. Beograd->Frankfurt) don't skew the positions.
    block_start = direct.find("Beograd->Pariz\n")
    assert block_start != -1, "Beograd->Pariz route header not found"
    block = direct[block_start:]
    pos_france = block.find("AirFrance")
    pos_srbia = block.find("AirSrbia")
    assert pos_france != -1, "AirFrance not found in Beograd->Pariz block"
    assert pos_srbia != -1, "AirSrbia not found in Beograd->Pariz block"
    assert pos_france < pos_srbia, "AirFrance should appear before AirSrbia"


# ===========================================================================
# Integration tests: flights_indirect.txt content
# ===========================================================================

@pytest.mark.parametrize("script", SCRIPTS)
def test_indirect_finds_connection_via_frankfurt(script):
    """Beograd->Pariz must find a valid connection through Frankfurt."""
    _, _, indirect = run_script(script, "Beograd->Pariz")
    assert "Frankfurt" in indirect


@pytest.mark.parametrize("script", SCRIPTS)
def test_indirect_excludes_impossible_connections(script):
    """Second leg that departs before the first leg arrives must be excluded."""
    flights = textwrap.dedent("""\
        AirSrbia|Beograd->Frankfurt|07:00-09:00,120.00
        EarlyBird|Frankfurt->Pariz|08:00-09:30,80.00
        Lufthansa|Frankfurt->Pariz|10:00-11:30,90.00
    """)
    _, _, indirect = run_script(script, "Beograd->Pariz", flights_content=flights)
    # EarlyBird departs 08:00, before AirSrbia arrives 09:00 → must be absent
    assert "EarlyBird" not in indirect
    # Lufthansa departs 10:00 > 09:00 → must be present
    assert "Lufthansa" in indirect


@pytest.mark.parametrize("script", SCRIPTS)
def test_indirect_empty_when_no_connection_exists(script):
    """If no valid connection exists, flights_indirect.txt must be empty."""
    flights = textwrap.dedent("""\
        AirSrbia|Beograd->Pariz|08:00-10:00,150.00
    """)
    _, _, indirect = run_script(script, "Beograd->Pariz", flights_content=flights)
    assert indirect.strip() == ""
