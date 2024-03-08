import requests
from bs4 import BeautifulSoup
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
import time

login_url = 'https://signin.siemens.com/regapi/Login?lang=en&app=MALL&ret=https%3a%2f%2fmall.industry.siemens.com%2fmall%2fen%2fWW%2fCatalog%2fProducts%2f10007359%3ftree%3dCatalogTree&hr=true'
motor_name = "1LE1001-1EA2.-...."  # Replace with the actual motor name
email = "jamesowys@gmail.com"  # Replace with your email
password = "Jamesowys2306!"  # Replace with your password

def fetch_webpage(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.content
    else:
        print("Failed to fetch data from the URL.")
        return None

def parse_webpage(content):
    return BeautifulSoup(content, 'html.parser')

def extract_motor_data(soup):
    # Extract title
    title_element = soup.find('span', class_='productIdentifier')
    if title_element:
        title = title_element.text.strip()
    else:
        title = "Title not found"

    # Extract abstract
    product_description = soup.find('div', class_='productdescription')
    if product_description:
        abstract = product_description.text.strip()
    else:
        abstract = "Abstract not found."

    # Extract picture URL
    picture_element = soup.find('img', class_='productPicture')
    if picture_element:
        picture_url = picture_element['src']
    else:
        picture_url = "Picture URL not found"

    # Extract file URL
    file_element = soup.find('a', class_='externalLink', text='Download')
    if file_element:
        file_url = file_element['href']
    else:
        file_url = "File URL not found"

    # Extract data from the "Product" section
    product_section = soup.find('table', class_='ProductDetailsTable')
    if product_section:
        product_data = {}  # Create an empty dictionary to store the product data
    
        # Find all rows within the product section
        product_rows = product_section.find_all('tr')
        for row in product_rows:
            data_labels = row.find_all('td', class_='productDetailsTable_DataLabel')
            data_values = row.find_all('td')[1:]  # Exclude the first td containing labels
    
            # Check if both labels and values are found
            if data_labels and data_values:
                for label, value in zip(data_labels, data_values):
                    header = label.text.strip()
                    value_text = value.text.strip()
                    product_data[header] = value_text  # Add the data to the dictionary


    # Construct the motor_data dictionary including safety manuals data
    motor_data = {
        "title": title,
        "abstract": abstract,
        "picture": picture_url,
        "file": file_url,
        "product_data": product_data,  # Add the extracted product data here

    }


    time.sleep(5)  # Sleep for 5 seconds

    return motor_data


def click_element(driver, element_xpath):
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, element_xpath)))
    element = driver.find_element(By.XPATH, element_xpath)
    element.click()
    
def extract_safety_manuals(driver):
    # Wait for the file_url element to be clickable
    file_element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//a[@class='externalLink' and text()='Download']")))
    
    # Get the href attribute of the file element
    file_url = file_element.get_attribute('href')
    
    # Open the URL in a new tab using JavaScript
    driver.execute_script("window.open(arguments[0], '_blank');", file_url)
    driver.switch_to.window(driver.window_handles[-1])
    time.sleep(3)
    
    # Wait for the page to load and find the element with class "fs-count"
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'fs-count')))
    
    # Find and click the element with class "num" and text "100" to show all entries
    show_all_element = driver.find_element(By.XPATH, "//span[@class='num' and text()='100']")
    show_all_element.click()
    time.sleep(2)

    # Wait for the page to load and find all documents with class "documentheader"
    
    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'documentheader')))
    document_elements = driver.find_elements(By.CLASS_NAME, 'documentheader')
    safety_manuals = []
    
    # Loop through the document elements and open links in new tabs
    for document_element in document_elements:
        # Get the inner HTML of the document element
        document_html = document_element.get_attribute('innerHTML')

        # Create a new BeautifulSoup object from the document_html
        document_soup = BeautifulSoup(document_html, 'html.parser')

        # Find the document link using BeautifulSoup
        document_link = document_soup.find('a', {'data-bind': lambda x: 'getDetailLink()' in x})

        if document_link:
            # Get the href attribute of the document link
            document_url = document_link['href']
            # Rest of your code for processing the document URL
            driver.execute_script("window.open(arguments[0], '_blank');", document_url)
            driver.switch_to.window(driver.window_handles[-1])
        
            # Find the PDF link element
            pdf_link = None
            try:
                pdf_link_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'PDF document')]")))
                pdf_link = pdf_link_element.find_element(By.XPATH, "../a").get_attribute('href')
            except:
                pass
        
            # Create a dictionary for this safety manual
            safety_manual = {
                "title": document_link.text,
                "pdf_link": pdf_link if pdf_link else "No PDF document available"
            }
            safety_manuals.append(safety_manual)
            
            # Close the current tab after processing the document
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            
    # Close the current tab after processing all documents
    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    
    return safety_manuals


def open_motor_links_in_tabs(driver, motor_names):
    for motor_name in motor_names:
        motor_url = f"https://mall.industry.siemens.com/mall/en/sg/Catalog/Product/?mlfb={motor_name}"
        
        # Open the URL in a new tab using JavaScript
        driver.execute_script("window.open(arguments[0], '_blank');", motor_url)
        
        # Switch to the new tab
        driver.switch_to.window(driver.window_handles[-1])
        
        # Perform your actions on the new tab
        time.sleep(3)  # You can replace this with the desired action
        
        close_guided_tour(driver)
        
        # Wait for the page to load (you might need to adjust the condition based on the actual behavior of the website)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'productdescription')))
        
        # Fetch the updated webpage content
        content = driver.page_source
        if content:
            soup = BeautifulSoup(content, 'html.parser')
            motor_data = extract_motor_data(soup)
            motor_data_list.append(motor_data)  # Append the motor_data dictionary to the list
            # Extract safety manuals

            safety_manuals = extract_safety_manuals(driver)  # You'll need to define this function
            motor_data_list.append(safety_manuals)
            
            print(f"Data for {motor_name}:", motor_data , safety_manuals)
        else:
            print(f"Failed to fetch data for {motor_name}")
        
        # Close the current tab and switch back to the original tab if needed
        driver.close()
        
        driver.switch_to.window(driver.window_handles[0])
        
        time.sleep(3)


def save_data_to_json(motor_data_list, file_path):
    full_file_path = r'C:\Users\joys_\Downloads\{}'.format(file_path)
    with open(full_file_path, 'w') as json_file:
        json.dump(motor_data_list, json_file, indent=4)
        
def get_current_url(driver):
    new_url = driver.current_url
    time.sleep(3)
    return new_url #overwrites a new url

def login_to_website(driver, email, password):
    driver.get(login_url)  # Go to the login URL
    
    # Find and fill in the email field
    email_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'login')))
    email_element.send_keys(email)
    time.sleep(2)
    
    # Find and click the "Next" button
    next_button = driver.find_element(By.XPATH, "//button[contains(@class, 'general-button--max-width') and contains(@class, 'variant-primary') and contains(@class, 'bg-light')]")
    next_button.click()
    
    # Find and fill in the password field
    password_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'password')))
    password_element.send_keys(password)
    time.sleep(2)
    
    # Find and click the "Login" button
    login_button = driver.find_element(By.XPATH, "//button[contains(@class, 'general-button--max-width') and contains(@class, 'variant-primary') and contains(@class, 'bg-light') and contains(.//span[@class='general-button__label-content'], 'Login')]")
    login_button.click()
    
    # Wait for successful login (you might need to adjust the condition based on the actual behavior of the website)
    WebDriverWait(driver, 10).until(EC.url_contains('mall.industry.siemens.com'))
    
    
def interact_with_hidden_element(driver, element):
    # Execute JavaScript to make the hidden element visible and clickable
    js_code = """
    var element = arguments[0];
    element.style.visibility = 'visible';
    element.style.display = 'block';
    element.click();
    """
    driver.execute_script(js_code, element)
    
def close_guided_tour(driver):
    try:
        guided_tour_close_element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "span.guided-tour-close")))
        guided_tour_close_element.click()
    except:
        pass
    
def scrape_product_data(url, motor_name, email, password):
    # Initialize the Chrome driver
    chrome_service = ChromeService(executable_path='C:/Users/joys_/Downloads/chromedriver_ver116/chromedriver-win64/chromedriver.exe')
    driver = webdriver.Chrome(service=chrome_service)
    
    # Login to the website
    login_to_website(driver, email, password)
    
    
    # Capture the page source after logging in
    time.sleep(5) #let the page load
    # page = driver.page_source
    # print (page)
    
    time.sleep(5) #for user to click reject cookies
    
    wait = WebDriverWait(driver, 10)
    
 # Check if "Close Guided Tour" element is present and click it
    try:
        guided_tour_close_element = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "span.guided-tour-close")))
        guided_tour_close_element.click()
    except:
        pass
    
    # Navigate to the desired URL
    desired_url = "https://mall.industry.siemens.com/mall/en/sg/Catalog/Products/10139508?tree=CatalogTree"
    driver.get(desired_url)
    time.sleep(3)
    
     # Check if "Close Guided Tour" element is present and click it
    close_guided_tour(driver)
    
    simotics_element = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[@class='fancytree-title' and text()='SIMOTICS GP 1LE1/1PC1 Standard Motors']")))
    simotics_element.click()
    
    close_guided_tour(driver)
    
    # Wait for the motor name elements to be clickable
    motor_name_elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//span[@class='productIdentifier']")))

    # Get the motor names from the current page
    motor_names = []
    for element in motor_name_elements:
        motor_names.append(element.text)
           
    # Now you have a list of all motor names on the current page
    print(motor_names)
    
    # # Click on the relevant elements
    time.sleep(3)
    # click_element(driver, "//span[@class='fancytree-title' and text()='SIMOTICS GP 1LE1/1PC1 Standard Motors']")
    open_motor_links_in_tabs(driver, motor_names)
    
    # After processing all motor links, save the list of motor_data dictionaries as JSON
    file_path = 'motor_data.json'
    save_data_to_json(motor_data_list, file_path)
    print("Data saved successfully as JSON.")
    
    # Quit the driver
    driver.quit()
    
    # return motor_data if needed
    # else:
    # # Quit the driver in case of content fetch failure
    #      driver.quit()
    #      return None


    #     return motor_data
    # else:
    #     return None

#Main code
motor_data_list = []  # Initialize an empty list to store motor_data
motor_data = scrape_product_data(login_url, motor_name, email, password)
