from fastapi import FastAPI
import time
import threading
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

app = FastAPI()

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

            page.goto(
                "https://www.dallascounty.org/jaillookup/search.jsp",
                timeout=60000
            )

            page.wait_for_timeout(3000)
            page.mouse.wheel(0, 1500)
            time.sleep(2)

            page.fill('input[name="caseNumber"]', case_number)
            page.click('input[value="Search By Case Number"]')

            page.wait_for_load_state("networkidle")
            time.sleep(2)

            html = page.content()
            browser.close()

        # --------------------
        # PARSE HTML
        # --------------------
        if "No records were found" in html:
            return {
                "found": False,
                "case_number": case_number
            }

        soup = BeautifulSoup(html, "html.parser")

        record = {}

        # Extract all table rows
        for row in soup.select("tr"):
            cols = row.find_all("td")
            if len(cols) == 2:
                label = cols[0].get_text(strip=True)
                value = cols[1].get_text(strip=True)

                if label and value:
                    record[label] = value

        if not record:
            return {
                "found": False,
                "case_number": case_number,
                "message": "Record page loaded but no data parsed"
            }

        return {
            "found": True,
            "case_number": case_number,
            "source": "Dallas County Jail Lookup",
            "record": record
        }
