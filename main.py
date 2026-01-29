from fastapi import FastAPI
import time
from playwright.sync_api import sync_playwright

app = FastAPI()

@app.get("/")
def root():
    return {"status": "alive"}

@app.get("/search/{case_number}")
def search(case_number: str):
    return lookup_case(case_number)

def lookup_case(case_number: str):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )

        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        )

        page.goto("https://www.dallascounty.org/jaillookup/search.jsp", timeout=60000)
        page.wait_for_timeout(3000)

        page.mouse.wheel(0, 1500)
        time.sleep(2)

        page.fill('input[name="caseNumber"]', case_number)
        page.click('input[value="Search By Case Number"]')

        page.wait_for_load_state("networkidle")
        time.sleep(3)

        text = page.inner_text("body")

        browser.close()

        if "No records were found" in text:
            return {"found": False}

        return {
            "found": True,
            "raw_text": text[:3000]
        }
