from fastapi import FastAPI
import time
import threading
import json
from playwright.sync_api import sync_playwright

app = FastAPI()

lock = threading.Lock()

def lookup_case(case_number):
    with lock:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)  # set True in prod!
            page = browser.new_page()

            # 1. Open website
            page.goto(
                "https://www.dallascounty.org/jaillookup/search.jsp",
                wait_until="domcontentloaded",
                timeout=80000
            )

            page.wait_for_timeout(5000)

            # 2. Scroll down (form is lower on page)
            page.mouse.wheel(0, 1500)
            time.sleep(2)

            # 3. Find case number input
            page.wait_for_selector('input[name="caseNumber"]', timeout=60000)
            page.fill('input[name="caseNumber"]', case_number)

            # 4. Click search button
            page.click('input[value="Search By Case Number"]')

            # 5. Wait for next page / result
            page.wait_for_load_state("networkidle")
            time.sleep(3)

            text = page.inner_text("body")

            # 6. Check "No records" message
            if "No records were found" in text:
                browser.close()
                return {
                    "found": False,
                    "case_number": case_number
                }

            # 7. Scrape all visible text (basic safe scrape)
            result = {
                "found": True,
                "case_number": case_number,
                "raw_text": text.strip()
            }

            browser.close()
            return result


@app.get("/")
def root():
    return {"status": "alive"}


@app.get("/search/{case_number}")
def search(case_number: str):
    try:
        return lookup_case(case_number)
    except Exception as e:
        return {"error": True, "message": str(e)}


# If you want to run locally as script (optional)
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(json.dumps({"error": "case_number_missing"}))
        exit(1)

    case_number = sys.argv[1]
    output = lookup_case(case_number)
    print(json.dumps(output))
