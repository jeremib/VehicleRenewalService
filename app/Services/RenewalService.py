from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from Models.QueryPriceRequest import QueryPriceRequest
from Models.CompleteTransactionRequest import CompleteTransactionRequest
import time


class RenewalService:

    def __init__(self, form_data: QueryPriceRequest | CompleteTransactionRequest):

        options = Options()
        options.add_argument("--headless")  # Add this line to enable headless mode
        options.add_argument("--no-sandbox")  # Optional: For environments like Docker
        options.add_argument("--disable-dev-shm-usage")  # Optional: Prevents memory issues in headless mode
        prefs = {"profile.managed_default_content_settings.images": 2}
        options.add_experimental_option("prefs", prefs)
        self.driver = webdriver.Chrome(options=options)

        self.form_data = form_data

    def wait_for_element(self, locator, timeout=10):
        """Wait for an element to be present in the DOM."""
        return WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located(locator))

    def fill_form_page(self):
        """Fill out the form with name, address, city, state, etc."""

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

    def submit_form(self):
        """Submit the form and handle validation errors."""

        try:
            submit_button = self.driver.find_element(By.ID, "payrenewal_None")
            self.driver.execute_script("arguments[0].click();", submit_button)
            time.sleep(4)

            try:
                validation_error = self.driver.find_element(By.CSS_SELECTOR, "div.swal2-header")

                self.retry_form_submission()
            except Exception as e:
              
                pass
        except Exception as e:
           
            pass

    def retry_form_submission(self):
        """Retry form submission if validation error occurs."""
        try:
            ok_button = self.driver.find_element(By.CSS_SELECTOR, "button.swal2-confirm.swal2-styled")
            self.driver.execute_script("arguments[0].click();", ok_button)
            self.submit_form()
        except Exception as e:
            pass

    def handle_alert(self):
        """Check for and handle an alert."""
        try:
            WebDriverWait(self.driver, 5).until(EC.alert_is_present())
            alert = self.driver.switch_to.alert
            alert_text = alert.text
            alert.accept()
            return alert_text
        except Exception as e:
            return None

    def search_plate_number(self):
        """Enter the plate number and proceed."""
        plate_input = self.wait_for_element((By.CSS_SELECTOR,
                                             "input[name='plateNumber']"))
        plate_input.send_keys(self.form_data.plateNumber)

        self.driver.execute_script("document.expressRenew.submit();")
        return self.handle_alert()

    def county_selection_element(self):
        """Handle county selection if needed."""
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

    def collect_form_data(self):
        """Scrape form data after successful submission."""
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
            pass
            return None

    def get_element_text_or_default(self, css_selector, default_value=""):
        """Get text of an element if it exists, otherwise return default."""
        try:
            return self.driver.find_element(By.CSS_SELECTOR, css_selector).text
        except Exception:
            return default_value

    def handle_payment_processing(self):
        """Handle payment processing within an iframe."""

        try:
            self.driver.switch_to.default_content()
            iframe = self.wait_for_element((By.CSS_SELECTOR, "#iframe"))
            self.driver.switch_to.frame(iframe)

            account_input = self.wait_for_element((By.ID, "payment-account"))
            account_input.send_keys(self.form_data.account)

            self.select_dropdown_option("#payment-expmonth-label > select", self.form_data.exp_month)
            self.select_dropdown_option("#payment-expyear-label > select", self.form_data.exp_year)

            cv_input = self.wait_for_element((By.CSS_SELECTOR, "#payment-cv-label > input[type=text]"))
            cv_input.send_keys(self.form_data.cv)

            submit_button = self.wait_for_element((By.CSS_SELECTOR, "#payment-submit-button"))
            submit_button.click()
            alert_text = self.handle_alert()

            if "Failed" in alert_text:
                return False
            return True  # Return fee summary after payment
        except Exception as e:

            return None
        finally:
            self.driver.switch_to.default_content()

    def check_current_page(self):
        """Determine whether we are on the street number page or form page."""
        try:
            street_input = self.driver.find_elements(By.CSS_SELECTOR, "#streetnum")
            if street_input:
                return "street_number_page"
            return "form_page"
        except Exception as e:

            return None

    def select_dropdown_option(self, selector, option_value):
        """Select an option from a dropdown."""
        select_element = Select(self.wait_for_element((By.CSS_SELECTOR, selector)))
        select_element.select_by_visible_text(option_value)

    def fill_street_number_page(self):
        """Fill out the street number page."""
        try:
            street_input = self.wait_for_element((By.CSS_SELECTOR, "#streetnum"))
            street_num = self.form_data.addressTwo.split(" ")[0]
            street_input.send_keys(street_num)

            plate_input = self.driver.find_element(By.CSS_SELECTOR, "#plateFields > div > input[name='platenum']")
            plate_input.send_keys(self.form_data.plateNumber)

            search_button = self.driver.find_element(By.ID, "Searchbutton")
            self.driver.execute_script("arguments[0].click();", search_button)

            # Collect additional form information
            self.collect_form_data()

        except Exception as e:
            pass
