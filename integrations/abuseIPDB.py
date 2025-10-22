import os
import re
import requests
from dotenv import load_dotenv

try:
    from rich.console import Console
    from rich.table import Table
    from rich.text import Text
    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# -------------------------------------------------------------------
# Configuration and constants
# -------------------------------------------------------------------

load_dotenv()
API_KEY = os.getenv("ABUSE_API_KEY")
API_URL = "https://api.abuseipdb.com/api/v2/check"

# IP address regex (valid IPv4)
IP_REGEX = re.compile(
    r"^(?:(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\.){3}"
    r"(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)$"
)

# Backward compatibility alias
ip_regex = IP_REGEX


# -------------------------------------------------------------------
# Core functionality
# -------------------------------------------------------------------

def abuse_ip(ip_address: str, return_json: bool = False):
    """
    Query AbuseIPDB for an IP reputation report.

    Args:
        ip_address (str): Target IP to query.
        return_json (bool): If True, return data as dict instead of printing.

    Returns:
        dict | None: Parsed AbuseIPDB data, or None on error.
    """

    # --- Validation ---
    if not API_KEY:
        print("[!] Missing API key. Set ABUSE_API_KEY in your environment or .env file.")
        return None

    if not IP_REGEX.match(ip_address):
        print(f"[!] Invalid IP address format: {ip_address}")
        return None

    headers = {
        "Key": API_KEY,
        "Accept": "application/json"
    }
    params = {
        "ipAddress": ip_address,
        "maxAgeInDays": 90,
        "verbose": True
    }

    try:
        response = requests.get(API_URL, headers=headers, params=params, timeout=10)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        print("[!] Request timed out. Please check your network.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[!] Error contacting AbuseIPDB: {e}")
        return None

    data = response.json().get("data", {})
    if not data:
        print("[!] No data returned from AbuseIPDB.")
        return None

    if return_json:
        return data

    _print_abuse_report(data)


# -------------------------------------------------------------------
# Pretty printing
# -------------------------------------------------------------------

def _print_abuse_report(data: dict):
    """Display AbuseIPDB results in a pretty table or plain text."""

    ip = data.get("ipAddress", "N/A")
    country = f"{data.get('countryName', 'N/A')} ({data.get('countryCode', '-')})"
    isp = data.get("isp", "N/A")
    domain = data.get("domain") or "N/A"
    usage = data.get("usageType", "N/A")
    abuse_score = data.get("abuseConfidenceScore", 0)
    reports = data.get("reports", [])
    total_reports = data.get("totalReports", 0)
    distinct_users = data.get("numDistinctUsers", 0)
    last_seen = data.get("lastReportedAt") or "N/A"

    # --- Fancy mode: rich output ---
    if RICH_AVAILABLE:
        console.print("\n[bold cyan]ABUSEIPDB IP REPUTATION REPORT[/bold cyan]\n")

        table = Table(show_header=False, expand=True)
        table.add_row("IP Address", ip)
        table.add_row("Country", country)
        table.add_row("ISP", isp)
        table.add_row("Domain", domain)
        table.add_row("Usage Type", usage)
        table.add_section()

        color = "green"
        if abuse_score >= 80:
            color = "red"
        elif abuse_score >= 40:
            color = "yellow"

        table.add_row("Abuse Score", Text(f"{abuse_score} / 100", style=color))
        table.add_row("Reports", f"{total_reports} (from {distinct_users} users)")
        table.add_row("Last Seen", last_seen)
        console.print(table)

        if reports:
            console.print("\n[bold]Recent Reports:[/bold]")
            for r in reports[:3]:
                console.print(
                    f"• [cyan]{r.get('reportedAt')}[/cyan] "
                    f"({r.get('reporterCountryName', 'Unknown')}) — "
                    f"[italic]{r.get('comment') or 'No comment'}[/italic]"
                )
        else:
            console.print("[green]No recent reports available.[/green]")

        console.print("=" * 60 + "\n")

    # --- Fallback mode: plain text ---
    else:
        print("=" * 60)
        print("ABUSEIPDB IP REPUTATION REPORT")
        print("=" * 60)
        print(f"IP Address : {ip}")
        print(f"Country    : {country}")
        print(f"ISP        : {isp}")
        print(f"Domain     : {domain}")
        print(f"Usage Type : {usage}")
        print("-" * 60)
        print(f"Abuse Score: {abuse_score} / 100")
        print(f"Reports    : {total_reports} (from {distinct_users} users)")
        print(f"Last Seen  : {last_seen}")
        print("-" * 60)

        if reports:
            print("Recent Reports:")
            for r in reports[:3]:
                print(f"  • Date     : {r.get('reportedAt')}")
                print(f"    Reporter : {r.get('reporterCountryName')}")
                print(f"    Comment  : {r.get('comment') or 'No comment'}")
                print(f"    Categories: {', '.join(map(str, r.get('categories', [])))}")
                print("-" * 60)
        else:
            print("No recent reports available.")
        print("=" * 60, "\n")


# -------------------------------------------------------------------
# Standalone testing
# -------------------------------------------------------------------

if __name__ == "__main__":
    ip = input("Enter IP address: ").strip()
    abuse_ip(ip)