import os
import time
import requests
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Progress tracker functions
def save_progress(doc_type, category_index, fund_index):
    """Save current progress to a file."""
    progress = {
        "doc_type": doc_type,
        "category_index": category_index,
        "fund_index": fund_index
    }
    with open("download_progress.json", "w") as f:
        json.dump(progress, f)
    print(f"Progress saved: {doc_type}, category {category_index}, fund {fund_index}")

def load_progress():
    """Load progress from file."""
    try:
        with open("download_progress.json", "r") as f:
            progress = json.load(f)
        print(f"Resuming from: {progress['doc_type']}, category {progress['category_index']}, fund {progress['fund_index']}")
        return progress["doc_type"], progress["category_index"], progress["fund_index"]
    except (FileNotFoundError, json.JSONDecodeError):
        print("No progress file found or invalid format. Starting from beginning.")
        return None, 0, 0

def download_sebi_documents(download_dir="downloads"):
    """Download KIM and SID PDFs from SEBI website."""
    # Create download directory
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
        print(f"Created download directory: {download_dir}")
    
    # Load progress if available
    last_doc_type, last_category_index, last_fund_index = load_progress()
    
    # Configure Chrome options
    chrome_options = webdriver.ChromeOptions()
    prefs = {
        'download.default_directory': os.path.abspath(download_dir),
        'download.prompt_for_download': False,
        'download.directory_upgrade': True,
        'plugins.always_open_pdf_externally': True
    }
    chrome_options.add_experimental_option('prefs', prefs)
    
    # Initialize driver
    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()
    
    try:
        # Determine where to start
        start_with_kim = last_doc_type is None or last_doc_type == "KIM"
        
        # Process KIM documents if needed
        if start_with_kim:
            kim_url = "https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doMutualFund=yes&mftype=3"
            print(f"\n--- Processing KIM documents ---")
            print(f"Navigating to KIM page: {kim_url}")
            driver.get(kim_url)
            
            # Wait for page to load
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
            print("KIM page loaded successfully.")
            
            # Find all links in the table (including JavaScript links)
            js_links = driver.find_elements(By.XPATH, "//table//a[contains(@onclick, 'getmutuakFund') or contains(@href, 'javascript:getmutuakFund')]")
            if not js_links:
                js_links = driver.find_elements(By.XPATH, "//table//a")
                print(f"Found {len(js_links)} links on KIM page, checking for JavaScript links...")
                
                # Filter for JavaScript links
                js_links = [link for link in js_links if 'javascript:' in link.get_attribute('href') or 'javascript:' in link.get_attribute('onclick') or 'getmutuakFund' in link.get_attribute('onclick')]
            
            print(f"Found {len(js_links)} mutual fund category links")
            
            # Process each category link
            for i, js_link in enumerate(js_links):
                # Skip categories we've already processed
                if last_doc_type == "KIM" and i < last_category_index:
                    print(f"Skipping already processed category {i+1}")
                    continue
                
                try:
                    category_name = js_link.text.strip()
                    print(f"Processing category {i+1}: {category_name}")
                    
                    # Click on the JavaScript link
                    js_link.click()
                    time.sleep(3)
                    
                    # Switch to the new tab if opened
                    if len(driver.window_handles) > 1:
                        driver.switch_to.window(driver.window_handles[-1])
                    
                    # Wait for fund list page to load
                    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
                    print("Fund list page loaded.")
                    
                    # Find all fund detail JavaScript links
                    fund_links = driver.find_elements(By.XPATH, "//table//a[contains(@onclick, 'getfundDetails') or contains(@href, 'javascript:getfundDetails')]")
                    if not fund_links:
                        fund_links = driver.find_elements(By.XPATH, "//table//a")
                        print(f"Found {len(fund_links)} links on fund list page, checking for JavaScript links...")
                        
                        # Filter for JavaScript links
                        fund_links = [link for link in fund_links if 'javascript:' in link.get_attribute('href') or 'javascript:' in link.get_attribute('onclick') or 'getfundDetails' in link.get_attribute('onclick')]
                    
                    print(f"Found {len(fund_links)} fund links")
                    
                    # Process each fund link
                    for j, fund_link in enumerate(fund_links):
                        # Skip funds we've already processed
                        if last_doc_type == "KIM" and i == last_category_index and j < last_fund_index:
                            print(f"Skipping already processed fund {j+1}")
                            continue
                        
                        try:
                            fund_name = fund_link.text.strip()
                            print(f"Processing fund {j+1}: {fund_name}")
                            
                            # Save current progress
                            save_progress("KIM", i, j)
                            
                            # Click on the fund link
                            fund_link.click()
                            time.sleep(3)
                            
                            # Switch to the new tab if opened
                            if len(driver.window_handles) > 2:
                                driver.switch_to.window(driver.window_handles[-1])
                            
                            # Wait for fund details page to load
                            time.sleep(3)
                            
                            # Look for the download button
                            try:
                                download_button = driver.find_element(By.CSS_SELECTOR, "#secondaryDownload")
                                print(f"Found download button for {fund_name}")
                                
                                # Create filename for checking if already downloaded
                                safe_name = fund_name.replace(" ", "_").replace("/", "_")
                                if not safe_name:
                                    safe_name = f"fund_{j+1}"
                                filename = f"{safe_name}_KIM.pdf"
                                filepath = os.path.join(download_dir, filename)
                                
                                # Check if file already exists
                                if os.path.exists(filepath):
                                    print(f"File already exists: {filename} - skipping download")
                                else:
                                    # Click the download button
                                    download_button.click()
                                    print(f"Clicked download button for {fund_name}")
                                    time.sleep(3)
                            except NoSuchElementException:
                                print(f"No download button found for {fund_name}")
                                
                                # Try alternative methods - look for iframe
                                try:
                                    iframe = driver.find_element(By.XPATH, "//iframe[contains(@src, '.pdf')]")
                                    src = iframe.get_attribute("src")
                                    if "file=" in src:
                                        pdf_url = src.split("file=")[1]
                                        if "&" in pdf_url:
                                            pdf_url = pdf_url.split("&")[0]
                                        
                                        # Create filename
                                        safe_name = fund_name.replace(" ", "_").replace("/", "_")
                                        if not safe_name:
                                            safe_name = f"fund_{j+1}"
                                        filename = f"{safe_name}_KIM.pdf"
                                        
                                        # Download PDF directly
                                        print(f"Downloading PDF from iframe: {pdf_url}")
                                        download_pdf(pdf_url, filename, download_dir)
                                except NoSuchElementException:
                                    print(f"No iframe found for {fund_name}")
                            
                            # Close fund details tab and switch back to fund list tab
                            if len(driver.window_handles) > 2:
                                driver.close()
                                driver.switch_to.window(driver.window_handles[-1])
                        except Exception as e:
                            print(f"Error processing fund {fund_name}: {str(e)}")
                            # Make sure we're back on the fund list tab
                            if len(driver.window_handles) > 2:
                                driver.close()
                                driver.switch_to.window(driver.window_handles[-1])
                    
                    # Close fund list tab and switch back to main tab
                    if len(driver.window_handles) > 1:
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                except Exception as e:
                    print(f"Error processing category {category_name}: {str(e)}")
                    # Make sure we're back on the main tab
                    while len(driver.window_handles) > 1:
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
            
            # Reset progress for SID
            save_progress("SID", 0, 0)
        
        # Process SID documents
        sid_url = "https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doMutualFund=yes&mftype=2"
        print(f"\n--- Processing SID documents ---")
        print(f"Navigating to SID page: {sid_url}")
        driver.get(sid_url)
        
        # Wait for page to load
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        print("SID page loaded successfully.")
        
        # Find all links in the table (including JavaScript links)
        js_links = driver.find_elements(By.XPATH, "//table//a[contains(@onclick, 'getmutuakFund') or contains(@href, 'javascript:getmutuakFund')]")
        if not js_links:
            js_links = driver.find_elements(By.XPATH, "//table//a")
            print(f"Found {len(js_links)} links on SID page, checking for JavaScript links...")
            
            # Filter for JavaScript links
            js_links = [link for link in js_links if 'javascript:' in link.get_attribute('href') or 'javascript:' in link.get_attribute('onclick') or 'getmutuakFund' in link.get_attribute('onclick')]
        
        print(f"Found {len(js_links)} mutual fund category links")
        
        # Process each category link
        for i, js_link in enumerate(js_links):
            # Skip categories we've already processed
            if last_doc_type == "SID" and i < last_category_index:
                print(f"Skipping already processed category {i+1}")
                continue
            
            try:
                category_name = js_link.text.strip()
                print(f"Processing category {i+1}: {category_name}")
                
                # Click on the JavaScript link
                js_link.click()
                time.sleep(3)
                
                # Switch to the new tab if opened
                if len(driver.window_handles) > 1:
                    driver.switch_to.window(driver.window_handles[-1])
                
                # Wait for fund list page to load
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
                print("Fund list page loaded.")
                
                # Find all fund detail JavaScript links
                fund_links = driver.find_elements(By.XPATH, "//table//a[contains(@onclick, 'getfundDetails') or contains(@href, 'javascript:getfundDetails')]")
                if not fund_links:
                    fund_links = driver.find_elements(By.XPATH, "//table//a")
                    print(f"Found {len(fund_links)} links on fund list page, checking for JavaScript links...")
                    
                    # Filter for JavaScript links
                    fund_links = [link for link in fund_links if 'javascript:' in link.get_attribute('href') or 'javascript:' in link.get_attribute('onclick') or 'getfundDetails' in link.get_attribute('onclick')]
                
                print(f"Found {len(fund_links)} fund links")
                
                # Process each fund link
                for j, fund_link in enumerate(fund_links):
                    # Skip funds we've already processed
                    if last_doc_type == "SID" and i == last_category_index and j < last_fund_index:
                        print(f"Skipping already processed fund {j+1}")
                        continue
                    
                    try:
                        fund_name = fund_link.text.strip()
                        print(f"Processing fund {j+1}: {fund_name}")
                        
                        # Save current progress
                        save_progress("SID", i, j)
                        
                        # Click on the fund link
                        fund_link.click()
                        time.sleep(3)
                        
                        # Switch to the new tab if opened
                        if len(driver.window_handles) > 2:
                            driver.switch_to.window(driver.window_handles[-1])
                        
                        # Wait for fund details page to load
                        time.sleep(3)
                        
                        # Look for the download button
                        try:
                            download_button = driver.find_element(By.CSS_SELECTOR, "#secondaryDownload")
                            print(f"Found download button for {fund_name}")
                            
                            # Create filename for checking if already downloaded
                            safe_name = fund_name.replace(" ", "_").replace("/", "_")
                            if not safe_name:
                                safe_name = f"fund_{j+1}"
                            filename = f"{safe_name}_SID.pdf"
                            filepath = os.path.join(download_dir, filename)
                            
                            # Check if file already exists
                            if os.path.exists(filepath):
                                print(f"File already exists: {filename} - skipping download")
                            else:
                                # Click the download button
                                download_button.click()
                                print(f"Clicked download button for {fund_name}")
                                time.sleep(3)
                        except NoSuchElementException:
                            print(f"No download button found for {fund_name}")
                            
                            # Try alternative methods - look for iframe
                            try:
                                iframe = driver.find_element(By.XPATH, "//iframe[contains(@src, '.pdf')]")
                                src = iframe.get_attribute("src")
                                if "file=" in src:
                                    pdf_url = src.split("file=")[1]
                                    if "&" in pdf_url:
                                        pdf_url = pdf_url.split("&")[0]
                                    
                                    # Create filename
                                    safe_name = fund_name.replace(" ", "_").replace("/", "_")
                                    if not safe_name:
                                        safe_name = f"fund_{j+1}"
                                    filename = f"{safe_name}_SID.pdf"
                                    
                                    # Download PDF directly
                                    print(f"Downloading PDF from iframe: {pdf_url}")
                                    download_pdf(pdf_url, filename, download_dir)
                            except NoSuchElementException:
                                print(f"No iframe found for {fund_name}")
                        
                        # Close fund details tab and switch back to fund list tab
                        if len(driver.window_handles) > 2:
                            driver.close()
                            driver.switch_to.window(driver.window_handles[-1])
                    except Exception as e:
                        print(f"Error processing fund {fund_name}: {str(e)}")
                        # Make sure we're back on the fund list tab
                        if len(driver.window_handles) > 2:
                            driver.close()
                            driver.switch_to.window(driver.window_handles[-1])
                
                # Close fund list tab and switch back to main tab
                if len(driver.window_handles) > 1:
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
            except Exception as e:
                print(f"Error processing category {category_name}: {str(e)}")
                # Make sure we're back on the main tab
                while len(driver.window_handles) > 1:
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
        
        print("\nAll documents processed successfully.")
        # Clear progress file when done
        if os.path.exists("download_progress.json"):
            os.remove("download_progress.json")
            print("Progress file cleared.")
    
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        driver.quit()
        print("Browser closed.")

def download_pdf(url, filename, download_dir):
    """Download PDF directly using requests."""
    filepath = os.path.join(download_dir, filename)
    
    # Check if file already exists
    if os.path.exists(filepath):
        print(f"File already exists: {filename} - skipping download")
        return True
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        print(f"Downloaded: {filename}")
        return True
    except Exception as e:
        print(f"Failed to download {url}: {str(e)}")
        return False

if __name__ == "__main__":
    download_sebi_documents()