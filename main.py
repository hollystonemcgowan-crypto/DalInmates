from fastapi import FastAPI
import time
import threading
from playwright.sync_api import sync_playwright

app = FastAPI()

# 🔒 Global lock to prevent parallel Playwright runs
lock = threading.Lock()


@app.get("/")
def root():
    return {"status": "alive"}


@app.get("/search/{case_number}")
def search(case_number: str):
    try:
        return lookup_case(case_number)
    except Exception as e:
        return {
            "error": True,
            "message": str(e)
        }


def lookup_case(case_number: str):
    # Only ONE Playwright execution at a time
    with lock:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage"
                ]
            )

            page = browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120 Safari/537.36"
                )
            )

            # Open Dallas County jail lookup page
            page.goto(
                "https://www.dallascounty.org/jaillookup/search.jsp",
                timeout=60000
            )

            # Let the page settle
            page.wait_for_timeout(3000)

            # Scroll to ensure inputs are visible
            page.mouse.wheel(0, 1500)
            time.sleep(2)

            # Fill and submit form
            page.fill('input[name="caseNumber"]', case_number)
            page.click('input[value="Search By Case Number"]')

            # Wait for results
            page.wait_for_load_state("networkidle")
            time.sleep(2)

            # ✅ SAFE extraction (no heavy rendering)
            html = page.content()

            browser.close()

            # Simple result detection
            if "No records were found" in html:
                return {
                    "found": False,
                    "case_number": case_number
                }

            return {
                "found": True,
                "case_number": case_number,
                "source": "Dallas County Jail Lookup",
                "html_length": len(html),
                "raw_html": html[:3000]  # limit size for n8n
            }
