import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from Models.QueryPriceRequest import QueryPriceRequest
from Models.CompleteTransactionRequest import CompleteTransactionRequest
import time
import os
from datetime import datetime
import random
import string


class RenewalService:

    def __init__(self, form_data: QueryPriceRequest | CompleteTransactionRequest):
        logging.basicConfig(level=logging.INFO)
        plate_info = f" [Plate: {form_data.plateNumber}]" if hasattr(form_data, 'plateNumber') else ""
        logging.info(f"Initializing RenewalService{plate_info}")

        options = Options()
        options.add_argument("--headless")  # Add this line to enable headless mode
        options.add_argument("--no-sandbox")  # Optional: For environments like Docker
        options.add_argument("--disable-dev-shm-usage")  # Optional: Prevents memory issues in headless mode
        prefs = {"profile.managed_default_content_settings.images": 2}
        options.add_experimental_option("prefs", prefs)
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-client-side-phishing-detection")
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-sync")

        self.driver = webdriver.Chrome(options=options)

        self.form_data = form_data

    def get_log_prefix(self):
        """Helper method to create consistent log prefix with plate number"""
        return f"[Plate: {self.form_data.plateNumber}]" if hasattr(self.form_data, 'plateNumber') else ""

    def wait_for_element(self, locator, timeout=10):
        logging.info(f"{self.get_log_prefix()} Waiting for element: {locator}")
        return WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located(locator))

    def fill_form_page(self):
        logging.info(f"{self.get_log_prefix()} Filling out the form page")

        try:
            form_fields = {
                "name": self.form_data.name,
                "addressTwo": self.form_data.addressTwo,
                "city": self.form_data.city,
                "state": self.form_data.state,
                "homePhone0": self.form_data.homePhone0,
                "homePhone1": self.form_data.homePhone1,
                "homePhone2": self.form_data.homePhone2,
                "email": self.form_data.email,
                "zip": self.form_data.zip
            }
            
            try:
                shelby_address_verify = self.driver.find_element(By.CSS_SELECTOR, "#shelby_address_verify")
                self.driver.execute_script("arguments[0].click();", shelby_address_verify)
                time.sleep(2)
                form_fields["confirmEmail"] = self.form_data.email #confirm email needed on shelby address verify
                logging.info(f"{self.get_log_prefix()} Shelby address verified successfully")
            except Exception as e:
                pass

            for field, value in form_fields.items():
                if field == 'zip':
                    try:

                        zip_element = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "#zip"))
                        )

                        # Once the name element is found, send the name to the input field
                        zip_element.send_keys(value)
                        time.sleep(2)
                    except Exception as e:
                        
                        time.sleep(2)
                else:
                    try:
                        
                        element = self.wait_for_element((By.CSS_SELECTOR, f"#{field}"))
                        element.send_keys(value)
                    except Exception as e:
                       pass

            confirm_email = self.wait_for_element((By.CSS_SELECTOR, "#confirmemail"))
            confirm_email.send_keys(self.form_data.email)

            self.submit_form()

        except Exception as e:
            
            pass

        logging.info(f"{self.get_log_prefix()} Form page filled successfully")

    def submit_form(self, attempt=0):
        logging.info(f"{self.get_log_prefix()} Submitting the form")

        try:
            submit_button = self.driver.find_element(By.ID, "payrenewal_None")
            self.driver.execute_script("arguments[0].click();", submit_button)
            time.sleep(4)

            try:
                validation_error = self.driver.find_element(By.CSS_SELECTOR, "div.swal2-header")
                if attempt < 3:
                    logging.info(f"{self.get_log_prefix()} Validation error found, retrying form submission")
                    self.retry_form_submission(attempt)
                else:
                    logging.error(f"{self.get_log_prefix()} Max attempts reached. Form submission failed.")
                    
            except Exception as e:
              
                pass
        except Exception as e:
           
            pass

        logging.info(f"{self.get_log_prefix()} Form submitted successfully")

    def retry_form_submission(self, attempt=0):
        logging.info(f"{self.get_log_prefix()} Retrying form submission")

        try:
            ok_button = self.driver.find_element(By.CSS_SELECTOR, "button.swal2-confirm.swal2-styled")
            self.driver.execute_script("arguments[0].click();", ok_button)
            self.submit_form(attempt + 1)
        except Exception as e:
            pass

        logging.info(f"{self.get_log_prefix()} Form submission retried successfully")

    def handle_alert(self):
        logging.info(f"{self.get_log_prefix()} Handling alert")

        try:
            WebDriverWait(self.driver, 5).until(EC.alert_is_present())
            alert = self.driver.switch_to.alert
            alert_text = alert.text
            alert.accept()
            return alert_text
        except Exception as e:
            return None

        logging.info(f"{self.get_log_prefix()} Alert handled successfully")

    def search_plate_number(self):
        logging.info(f"{self.get_log_prefix()} Searching for plate number")

        plate_input = self.wait_for_element((By.CSS_SELECTOR,
                                             "input[name='plateNumber']"))
        plate_input.send_keys(self.form_data.plateNumber)

        self.driver.execute_script("document.expressRenew.submit();")
        return self.handle_alert()

        logging.info(f"{self.get_log_prefix()} Plate number searched successfully")
        
    def beginning_county_selection(self):
        logging.info(f"{self.get_log_prefix()} Beginning county selection 2")

        try:
            select_element = Select(self.wait_for_element((By.CSS_SELECTOR,
                                             "select[name='countylist']")))
            for option in select_element.options:
                if self.form_data.county.upper() in option.text.upper():
                    select_element.select_by_visible_text(option.text)
                    logging.info(f"{self.get_log_prefix()} Selected county: {option.text}")
                    break
        except Exception as e:
            pass
       
        time.sleep(2) 
        # should take us to the available online services, let's find the plate renewals link and click it
        try:
            forms = self.driver.find_elements(By.CSS_SELECTOR, "form[name^='myform']")
            if forms:
                plate_renewal_form = forms[0]
                plate_renewal_form.submit()
            # plate_renewal_link = self.wait_for_element((By.CSS_SELECTOR, "span:contains('Plate Renewals')"))
            # plate_renewal_link.click()
            logging.info(f"{self.get_log_prefix()} Clicked on Plate Renewals link")
        except Exception as e:
            logging.error(f"{self.get_log_prefix()} Error clicking on Plate Renewals link: {e}") 


    def county_selection_element(self):
        logging.info(f"{self.get_log_prefix()} Selecting county")
        try:
            select_element = Select(self.wait_for_element((By.ID, "newCountyID")))
            for option in select_element.options:
                if self.form_data.county in option.text:
                    select_element.select_by_visible_text(option.text)
                    break
            submit_button = self.driver.find_element(By.ID, "zipCodeSubmit")
            submit_button.click()
        except Exception as e:
            pass

        logging.info(f"{self.get_log_prefix()} County selected successfully")

    def collect_form_data(self):
        logging.info(f"{self.get_log_prefix()} Collecting form data")

        try:
            fee_summary = {
                "County": self.get_element_text_or_default(".row > .col-md-2:nth-child(2) div:nth-child(2)"),
                "License": self.get_element_text_or_default(".row > .col-md-2:nth-child(3) div:nth-child(2)"),

                "Make": self.get_element_text_or_default(".row > .col-md-2:nth-child(4) div:nth-child(2)"),
                "Year": self.get_element_text_or_default(".row > .col-md-2:nth-child(5) div:nth-child(2)"),
                "Exp Date": self.get_element_text_or_default(".row > .col-md-2:nth-child(6) div:nth-child(2)"),
                
                "Registration": self.driver.find_element(By.CSS_SELECTOR, "#Registration\\ Display").text.replace("$", ""),
                "Online Fee": self.get_element_text_or_default("#Online\\ Fee\\ Display").replace("$", ""),
                "Organ Donor Amount": self.get_element_text_or_default("#Organ\\ Donor\\ Amount\\ Display").replace("$", ""),
                "County Wheel Tax": self.get_element_text_or_default("#County\\ Wheel\\ Tax\\ Display").replace("$", ""),
                "City Wheel Tax": self.get_element_text_or_default("#City\\ Wheel\\ Tax\\ Display").replace("$", ""),
                "Mail Fee": self.driver.find_element(By.CSS_SELECTOR, "#Mail\\ Fee\\ Display").text.replace("$", ""),
                "Subtotal": self.driver.find_element(By.CSS_SELECTOR, "#Subtotal\\ Display").text.replace("$", ""),
                "Processing Fee": self.driver.find_element(By.CSS_SELECTOR, "#Processing\\ Fee\\ Display").text.replace("$", ""),
                "Total": self.driver.find_element(By.CSS_SELECTOR, "#Total\\ Display").text.replace("$", "")
            }
            return fee_summary
        except Exception as e:
            print(f"Found an exception {e}")
            pass
            return None

        logging.info(f"{self.get_log_prefix()} Form data collected successfully")

    def get_element_text_or_default(self, css_selector, default_value=""):
        logging.info(f"{self.get_log_prefix()} Getting text for element: {css_selector}")

        try:
            return self.driver.find_element(By.CSS_SELECTOR, css_selector).text
        except Exception:
            return default_value

    def pop_up_in_payment_processing(self):
        logging.info(f"{self.get_log_prefix()} Handling pop-up in payment processing")
                                
        try:
            pop_up_text=self.wait_for_element((By.CSS_SELECTOR,"#swal2-title"))

            pop_ok_button=self.wait_for_element((By.CSS_SELECTOR, "button.swal2-confirm.swal2-styled"))
            pop_ok_button.click()
            
            try:
                check_terms_condition=self.wait_for_element((By.CSS_SELECTOR,"#acceptTerms_credit"))

                check_terms_condition.click()
            except Exception as e:
                print(f"Having error in checking terms {e}")
            
        except Exception as e:
            pass

        logging.info(f"{self.get_log_prefix()} Pop-up handled successfully")

    def handle_payment_processing(self):
        logging.info(f"{self.get_log_prefix()} Handling payment processing")

        try:
            fee_summary=self.collect_form_data()
            self.driver.switch_to.default_content()


            
            check_terms_condition=self.wait_for_element((By.CSS_SELECTOR,"#acceptTerms_credit"))
            self.driver.execute_script("arguments[0].click();", check_terms_condition)


            
            iframe = self.wait_for_element((By.CSS_SELECTOR, "#iframe"))
            self.driver.switch_to.frame(iframe)

            account_input = self.wait_for_element((By.ID, "payment-account"))
            account_input.send_keys(self.form_data.account)
            self.select_dropdown_option("#payment-expmonth-label > select", self.form_data.exp_month)
            self.select_dropdown_option("#payment-expyear-label > select", self.form_data.exp_year[-2:])
            cv_input = self.wait_for_element((By.CSS_SELECTOR, "#payment-cv-label > input[type=text]"))
            cv_input.send_keys(self.form_data.cv)
            submit_button = self.wait_for_element((By.CSS_SELECTOR, "#payment-submit-button"))
            self.driver.execute_script("arguments[0].click();", submit_button)
            
            
            alert_text = self.handle_alert()
            
            print(f" Alert text found here is the alert text {alert_text}")
            if alert_text:
                return alert_text
             
            return fee_summary  # Return fee summary after payment
        except Exception as e:
            raise f"Error in Payment Process {e}"
        finally:
            self.driver.switch_to.default_content()

        logging.info(f"{self.get_log_prefix()} Payment processed successfully")

    def check_current_page(self):
        logging.info(f"{self.get_log_prefix()} Checking current page: {self.driver.current_url}")
        try:
            normalized_url = self.driver.current_url.replace('//', '/')
            if 'renewalconfirm' in normalized_url:
                return "successful_payment"
            street_input = self.driver.find_elements(By.CSS_SELECTOR, "#streetnum")
            if street_input:
                return "street_number_page"
            return "form_page"
        except Exception as e:

            return None

    def select_dropdown_option(self, selector, option_value):
        logging.info(f"{self.get_log_prefix()} Selecting dropdown option: {selector} -> {option_value}")

        select_element = Select(self.wait_for_element((By.CSS_SELECTOR, selector)))
        select_element.select_by_visible_text(option_value)

    def fill_street_number_page(self):
        logging.info(f"{self.get_log_prefix()} Filling out the street number page")

        try:
            try:
                street_input = self.wait_for_element((By.CSS_SELECTOR, "#streetnum"))
                street_num = self.form_data.addressTwo.split(" ")[0]
                street_input.send_keys(street_num)
            except Exception as e:
                logging.error(f"{self.get_log_prefix()} Street number input not found: {e}")
                pass 


            plate_input = self.driver.find_element(By.CSS_SELECTOR, "#plateFields > div > input[name='platenum']")
            plate_input.send_keys(self.form_data.plateNumber)

            search_button = self.driver.find_element(By.ID, "Searchbutton")
            self.driver.execute_script("arguments[0].click();", search_button)
            
            alert_text = self.handle_alert()
            
            print(f" Alert text found here is the alert text {alert_text}")
            if alert_text:
                return alert_text 

            # Collect additional form information
            # self.collect_form_data()

        except Exception as e:
            pass

        logging.info(f"{self.get_log_prefix()} Street number page filled successfully")
        
    def save_screenshot(self):
        logging.info(f"{self.get_log_prefix()} Saving screenshot")
        try:
            # Create a folder based on the plate number
            folder_path = os.path.join(os.getcwd(), f"screenshots/{self.form_data.plateNumber}")
            os.makedirs(folder_path, exist_ok=True)

            random_chars = ''.join(random.choices(string.ascii_letters + string.digits, k=3))
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + random_chars
            screenshot_path = os.path.join(folder_path, f"screenshot_{timestamp}.png")
            self.driver.save_screenshot(screenshot_path)
            logging.info(f"{self.get_log_prefix()} Screenshot saved at {screenshot_path}")
        except Exception as e:
            logging.error(f"{self.get_log_prefix()} Failed to save screenshot: {e}")