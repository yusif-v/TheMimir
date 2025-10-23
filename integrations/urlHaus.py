"""
URLHaus Integration Module
--------------------------
Performs malicious URL lookups using the URLHaus API.

Usage:
    from integrations import urlHaus
    urlHaus.url_lookup("http://malicious.example.com")

Environment:
    ACH_API_KEY (optional) — used for authenticated queries if required.
"""

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
# Setup
# -------------------------------------------------------------------

load_dotenv()
API_KEY = os.getenv("ACH_API_KEY")
API_URL = "https://urlhaus-api.abuse.ch/v1/url/"

URL_REGEX = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE)
url_regex = URL_REGEX  # backward-compatibility alias


# -------------------------------------------------------------------
# Core Functionality
# -------------------------------------------------------------------

def url_lookup(input_url: str, return_json: bool = False):
    if not URL_REGEX.match(input_url):
        print(f"[!] Invalid URL format: {input_url}")
        return None

    headers = {"Auth-Key": API_KEY} if API_KEY else {}
    data = {"url": input_url}

    try:
        response = requests.post(API_URL, headers=headers, data=data, timeout=10)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        print("[!] Request timed out contacting URLHaus.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[!] Network error: {e}")
        return None

    try:
        json_resp = response.json()
    except ValueError:
        print("[!] Invalid JSON response from URLHaus.")
        return None

    if json_resp.get("error") == "Unauthorized":
        print("[!] Unauthorized: Check your ACH_API_KEY if required by the API.")
        return json_resp

    status = json_resp.get("query_status")
    if status == "ok":
        if return_json:
            return json_resp
        _print_url_report(json_resp)
    elif status == "no_results":
        print("[-] URL not found in URLHaus database.")
    else:
        print(f"[!] Unexpected API response: {status}")
        print(json_resp)

    return json_resp


# -------------------------------------------------------------------
# Pretty Printing
# -------------------------------------------------------------------

def _print_url_report(data: dict):
    """Display URLHaus report nicely in the terminal."""
    url = data.get("url") or "N/A"
    threat = data.get("threat") or "Unknown"
    status = data.get("url_status") or "N/A"
    date_added = data.get("date_added") or "N/A"
    reporter = data.get("reporter") or "N/A"
    tags = ", ".join(data.get("tags", [])) or "None"
    payloads = data.get("payloads", [])

    # --- Rich output ---
    if RICH_AVAILABLE:
        console.print("\n[bold cyan]URLHAUS THREAT INTELLIGENCE REPORT[/bold cyan]\n")

        table = Table(show_header=False, expand=True)
        table.add_row("URL", Text(url, style="cyan"))
        table.add_row("Threat", threat)
        table.add_row("Status", status)
        table.add_row("First Seen", date_added)
        table.add_row("Reporter", reporter)
        table.add_row("Tags", tags)
        console.print(table)

        if payloads:
            console.print("\n[bold]Associated Payloads:[/bold]")
            for p in payloads[:5]:
                fname = p.get("file_name") or p.get("payload_filename") or "N/A"
                ftype = p.get("file_type") or p.get("payload_type") or "N/A"
                sha256 = p.get("sha256_hash") or p.get("payload_sha256") or "N/A"
                console.print(f"• [yellow]{fname}[/yellow] ({ftype}) — SHA256: {sha256}")
        else:
            console.print("[green]No associated payloads found.[/green]")

        console.print("=" * 60 + "\n")

    # --- Plain text fallback ---
    else:
        print("=" * 60)
        print("URLHAUS THREAT INTELLIGENCE REPORT")
        print("=" * 60)
        print(f"URL        : {url}")
        print(f"Threat     : {threat}")
        print(f"Status     : {status}")
        print(f"First Seen : {date_added}")
        print(f"Reporter   : {reporter}")
        print(f"Tags       : {tags}")
        print("-" * 60)

        if payloads:
            print("Associated Payloads:")
            for p in payloads[:5]:
                fname = p.get("file_name") or p.get("payload_filename") or "N/A"
                ftype = p.get("file_type") or p.get("payload_type") or "N/A"
                sha256 = p.get("sha256_hash") or p.get("payload_sha256") or "N/A"
                print(f"  • {fname} ({ftype}) | SHA256: {sha256}")
        else:
            print("No associated payloads found.")
        print("=" * 60, "\n")


# -------------------------------------------------------------------
# CLI entry point
# -------------------------------------------------------------------

if __name__ == "__main__":
    url_input = input("Enter URL: ").strip()
    url_lookup(url_input)