import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

def scrape_uttamis_to_csv(output_csv="data/data.csv"):
    """
    Scrapes the fund-performance table from uttamis.co.tz
    across all pages (50 rows per page) and saves to CSV.
    Uses DataTables’ JS API—no clicking required.
    """
    url = "https://uttamis.co.tz/fund-performance"

    # 1. Configure headless Chrome
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    # suppress unwanted logs
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 60) # this is for timeout 

    try:
        driver.get(url)

        # Wait for initial table load indicator to disappear
        processing = (By.ID, "data_table_processing")
        wait.until(EC.invisibility_of_element_located(processing))

        # 2. Set “Show entries” to 5000
        select_box = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "select.form-select")))
        Select(select_box).select_by_value("5000") # this is the value for the entries 
        wait.until(EC.invisibility_of_element_located(processing))

        # 3. Read header row from the table
        header_cells = driver.find_elements(By.CSS_SELECTOR, "#data_table thead th")
        headers = [th.text.strip() for th in header_cells]

        # 4. Determine total number of pages via DataTables API
        total_pages = driver.execute_script(
            "return $('#data_table').DataTable().page.info().pages;"
        )
        print(f"Total pages detected: {total_pages}")

        # 5. Open CSV file and write header
        with open(output_csv, mode="w", newline="", encoding="utf-8") as f_out:
            writer = csv.writer(f_out)
            writer.writerow(headers)

            # 6. Loop through each page index
            for page_idx in range(total_pages):
                current_page = page_idx + 1
                print(f"Scraping page {current_page} of {total_pages}…")

                # Wait for any reload to finish
                wait.until(EC.invisibility_of_element_located(processing))

                # 7. Extract all rows on the current page
                rows = driver.find_elements(By.CSS_SELECTOR, "#data_table tbody tr")
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    writer.writerow([cell.text.strip() for cell in cells])

                # 8. Jump to the next page (if not last)
                if page_idx < total_pages - 1:
                    driver.execute_script(
                        "$('#data_table').DataTable().page(%s).draw(false);" % (page_idx + 1)
                    )
                    # slight pause for redraw
                    time.sleep(0.5)

        print(f"\n Data successfully written to '{output_csv}'")

    except Exception as e:
        print(f"\n ERROR: {e}")
        driver.save_screenshot("uttamis_scrape_error.png")
        print("Screenshot saved: uttamis_scrape_error.png")

    finally:
        driver.quit()
        print(" Chrome driver closed.")


if __name__ == "__main__":
    scrape_uttamis_to_csv()

# for any issues check and i will refine it for you doctor