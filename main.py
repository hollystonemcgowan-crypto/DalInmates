import sys
import json
import time
from playwright.sync_api import sync_playwright

def lookup_case(case_number):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # 1. Open website
        page.goto(
    "https://www.dallascounty.org/jaillookup/search.jsp",
    wait_until="domcontentloaded",
    timeout=60000
)


        
        page.wait_for_timeout(3000)
        # 2. Scroll down (form is lower on page)
        page.mouse.wheel(0, 1500)
        time.sleep(2)

        # 3. Find case number input
        page.wait_for_selector('input[name="caseNumber"]', timeout=30000)
        page.fill('input[name="caseNumber"]', case_number)

        # 4. Click search button
        page.click('input[value="Search By Case Number"]')

        # 5. Wait for next page / result
        page.wait_for_load_state("networkidle")
        time.sleep(3)

        content = page.content()
        text = page.inner_text("body")

        # 6. Check "No records" message
        if "No records were found" in text:
            browser.close()
            return {
                "found": False
            }

        # 7. Scrape all visible text (basic safe scrape)
        result = {
            "found": True,
            "raw_text": text.strip()
        }

        browser.close()
        return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "case_number_missing"}))
        sys.exit(1)

    case_number = sys.argv[1]
    output = lookup_case(case_number)

    print(json.dumps(output))
