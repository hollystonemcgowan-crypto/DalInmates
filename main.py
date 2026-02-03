from fastapi import FastAPI
import time
import threading
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

app = FastAPI()
lock = threading.Lock()

def lookup_case(case_number):
    try:
        with lock:
            with sync_playwright() as p:
                print("[INFO] Launching browser...")
                browser = p.chromium.launch(headless=True)  # Requires X server / GUI
                page = browser.new_page()

                print("[INFO] Opening Dallas County Jail Lookup page...")
                page.goto(
                    "https://www.dallascounty.org/jaillookup/search.jsp",
                    wait_until="domcontentloaded",
                    timeout=90000
                )

                time.sleep(2)
                page.mouse.wheel(0, 1500)
                time.sleep(2)

                print(f"[INFO] Filling case number: {case_number}")
                page.wait_for_selector('input[name="caseNumber"]', timeout=80000)
                page.fill('input[name="caseNumber"]', case_number)

                print("[INFO] Clicking Search button...")
                page.click('input[value="Search By Case Number"]')

                print("[INFO] Waiting for results...")
                page.wait_for_load_state("networkidle")
                time.sleep(3)

                body_text = page.inner_text("body")

                if "No records were found" in body_text:
                    print("[INFO] No records found for this case number.")
                    browser.close()
                    return {"found": False}

                # Click the first defendant link that starts with "defendant_detail"
                print("[INFO] Clicking defendant link...")
                try:
                    page.wait_for_selector('a[href^="defendant_detail"]', timeout=60000)
                    page.click('a[href^="defendant_detail"]')
                except PlaywrightTimeoutError:
                    print("[ERROR] Defendant link not found.")
                    browser.close()
                    return {"found": False, "error": "Defendant link not found"}

                print("[INFO] Waiting for detail page to load...")
                page.wait_for_load_state("networkidle")
                time.sleep(3)

                detail_text = page.inner_text("body")
                print("[INFO] Scraping completed.")

                browser.close()
                return {"found": True, "detail_text": detail_text.strip()}

    except Exception as e:
        print("[ERROR] Exception occurred:")
        import traceback
        traceback.print_exc()
        return {"found": False, "error": str(e)}

@app.get("/")
def root():
    return {"status": "alive"}

@app.get("/search/{case_number}")
def search(case_number: str):
    return lookup_case(case_number)


