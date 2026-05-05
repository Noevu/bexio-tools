#!/usr/bin/env python3
"""
Sync Bexio outgoing invoices to Notion with PDF attachments.

Usage:
  python notion-sync.py              # sync all unsynced invoices
  python notion-sync.py --id 303     # sync specific invoice
  python notion-sync.py --since 2026-01-01  # sync since date
  python notion-sync.py --dry-run    # preview without creating
"""
import argparse
import base64
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

# ------------------------------------------------------------------
# Config
# ------------------------------------------------------------------
NOTION_DB_ID = "a44e791a-9bfa-8205-b3e1-870753001676"
NOTION_VERSION = "2022-06-28"
BEXIO_BASE = "https://api.bexio.com/2.0"
NOTION_BASE = "https://api.notion.com/v1"


def get_token(keychain_service: str) -> str:
    import subprocess
    result = subprocess.run(
        ["security", "find-generic-password", "-s", keychain_service, "-w"],
        capture_output=True, text=True,
    )
    token = result.stdout.strip()
    if not token:
        raise RuntimeError(f"No token in Keychain for service '{keychain_service}'")
    return token


# ------------------------------------------------------------------
# Bexio API
# ------------------------------------------------------------------
def bexio_get(path: str, token: str) -> dict | list:
    req = urllib.request.Request(
        f"{BEXIO_BASE}/{path}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def bexio_list_invoices(token: str, since: str | None = None) -> list:
    invoices = bexio_get("kb_invoice?order_by=id_desc&limit=500", token)
    if since:
        invoices = [i for i in invoices if i["is_valid_from"] >= since]
    return invoices


def bexio_download_pdf(invoice_id: int, token: str) -> tuple[bytes, str]:
    """Returns (pdf_bytes, filename)."""
    data = bexio_get(f"kb_invoice/{invoice_id}/pdf", token)
    return base64.b64decode(data["content"]), data["name"]


# ------------------------------------------------------------------
# Notion API helpers
# ------------------------------------------------------------------
def notion_request(method: str, path: str, token: str, body: dict | None = None) -> dict:
    url = f"{NOTION_BASE}/{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"Notion API {method} {path} → {e.code}: {body}") from e


def notion_upload_pdf(pdf_bytes: bytes, filename: str, token: str) -> str:
    """Upload PDF to Notion, return file_upload_id."""
    # 1. Create upload session
    created = notion_request("POST", "file_uploads", token, {
        "mode": "single_part",
        "filename": filename,
        "content_type": "application/pdf",
    })
    upload_id = created["id"]

    # 2. Send file via multipart/form-data
    boundary = "----BexioNotionBoundary7f3k9p"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: application/pdf\r\n\r\n"
    ).encode() + pdf_bytes + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"{NOTION_BASE}/file_uploads/{upload_id}/send",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    with urllib.request.urlopen(req) as r:
        json.loads(r.read())

    return upload_id


def notion_find_by_referenz(referenz: str, token: str) -> dict | None:
    """Query Notion DB for page with matching Referenz. Returns page or None."""
    result = notion_request("POST", f"databases/{NOTION_DB_ID}/query", token, {
        "filter": {
            "property": "Referenz",
            "rich_text": {"equals": referenz},
        },
        "page_size": 1,
    })
    results = result.get("results", [])
    return results[0] if results else None


def notion_create_invoice_page(inv: dict, file_upload_id: str, token: str) -> dict:
    """Create Notion page for a Bexio invoice with attached PDF."""
    doc_nr = inv["document_nr"]
    referenz = _extract_doc_number(doc_nr)
    client = _extract_client(inv)
    name = f"{client} — {referenz}"

    properties: dict = {
        "Name": {"title": [{"text": {"content": name}}]},
        "Absender": {"rich_text": [{"text": {"content": client}}]},
        "Betrag": {"number": float(inv["total"])},
        "Währung": {"select": {"name": "CHF"}},
        "date:Rechnungsdatum:start": inv["is_valid_from"],
        "date:Fällig am:start": inv["is_valid_to"],
        "Typ": {"select": {"name": "Rechnung"}},
        "Firma": {"select": {"name": "Noevu GmbH"}},
        "Referenz": {"rich_text": [{"text": {"content": referenz}}]},
        "Zahlung": {"select": {"name": "Offen"}},
        "Erfasst von": {"select": {"name": "Jarvis"}},
        "Attachment": {
            "files": [{
                "type": "file_upload",
                "name": f"{referenz}.pdf",
                "file_upload": {"id": file_upload_id},
            }]
        },
    }

    return notion_request("POST", "pages", token, {
        "parent": {"database_id": NOTION_DB_ID},
        "properties": properties,
    })


def notion_attach_to_existing(page_id: str, file_upload_id: str, filename: str, token: str):
    """Add attachment to existing Notion page."""
    notion_request("PATCH", f"pages/{page_id}", token, {
        "properties": {
            "Attachment": {
                "files": [{
                    "type": "file_upload",
                    "name": filename,
                    "file_upload": {"id": file_upload_id},
                }]
            }
        }
    })


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def _extract_doc_number(document_nr: str) -> str:
    """Extract just the invoice number from Bexio document_nr like '04.05.2026 2202-000223'."""
    parts = document_nr.split(" ")
    return parts[-1] if len(parts) > 1 else document_nr


def _extract_client(inv: dict) -> str:
    """Extract company/client name from contact_address."""
    address = inv.get("contact_address", "")
    if address:
        return address.split("\n")[0].strip()
    return inv.get("title", "Unknown")


def _has_attachment(page: dict) -> bool:
    files = page.get("properties", {}).get("Attachment", {}).get("files", [])
    return len(files) > 0


# ------------------------------------------------------------------
# Main sync
# ------------------------------------------------------------------
def sync_invoice(inv: dict, bexio_token: str, notion_token: str, dry_run: bool):
    doc_nr = inv["document_nr"]
    referenz = _extract_doc_number(doc_nr)
    client = _extract_client(inv)
    invoice_id = inv["id"]

    print(f"  [{invoice_id}] {referenz} — {client} ({inv['total']} CHF)", end="")

    existing = notion_find_by_referenz(referenz, notion_token)
    if existing and _has_attachment(existing):
        print(" → already in Notion with attachment, skip")
        return

    if dry_run:
        action = "create" if not existing else "attach"
        print(f" → [dry-run] would {action}")
        return

    # Download PDF from Bexio
    pdf_bytes, filename = bexio_download_pdf(invoice_id, bexio_token)

    # Upload to Notion
    file_upload_id = notion_upload_pdf(pdf_bytes, filename, notion_token)

    if existing:
        notion_attach_to_existing(existing["id"], file_upload_id, filename, notion_token)
        print(f" → attached PDF to existing page")
    else:
        page = notion_create_invoice_page(inv, file_upload_id, notion_token)
        print(f" → created {page['url']}")


def main():
    parser = argparse.ArgumentParser(description="Sync Bexio invoices → Notion")
    parser.add_argument("--id", type=int, help="Sync single invoice by Bexio ID")
    parser.add_argument("--since", help="Sync invoices since date (YYYY-MM-DD)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without creating")
    args = parser.parse_args()

    bexio_token = get_token("BEXIO_ACCESS_TOKEN")
    notion_token = get_token("NOTION_API_TOKEN")

    print("Fetching Bexio invoices...")

    if args.id:
        invoices = [bexio_get(f"kb_invoice/{args.id}", bexio_token)]
    else:
        invoices = bexio_list_invoices(bexio_token, since=args.since)

    print(f"Found {len(invoices)} invoice(s) to process\n")

    ok = err = 0
    for inv in invoices:
        try:
            sync_invoice(inv, bexio_token, notion_token, dry_run=args.dry_run)
            ok += 1
        except Exception as e:
            print(f" → ERROR: {e}")
            err += 1

    print(f"\nDone: {ok} synced, {err} errors")


if __name__ == "__main__":
    main()
