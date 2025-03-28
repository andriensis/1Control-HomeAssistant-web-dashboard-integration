import appdaemon.plugins.hass.hassapi as hass
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class GateBackend(hass.Hass):
  def initialize(self):
    self.log("1Control gate integration started")

    self.onecontrol_email = 'email' # IMPORTANT: update this with your 1control web email
    self.onecontrol_password = 'password' # IMPORTANT: update this with your 1control web password
    self.onecontrol_device_id = 'device_id' # IMPORTANT: update this with your 1control device id (you get it from the URL of your 1control device on the web dashboard)
    self.homeassistant_input_boolean = 'input_boolean.1control_gate_helper'

    self.hass = self.get_plugin_api("hass")
    self.listen_state(self.print_entity,self.homeassistant_input_boolean)

    self.log("Logging into 1Control web")
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--headless')
    self.driver = webdriver.Chrome(options)
    wait = WebDriverWait(self.driver, 15)
    self.driver.get('https://web.1control.eu/')
    self.driver.find_element(By.ID, 'userEmail').send_keys(self.onecontrol_email)
    self.driver.find_element(By.ID, 'userPassword').send_keys(self.onecontrol_password)
    self.driver.find_element(By.XPATH, '/html/body/app-root/div/main/app-login/section[2]/div/div/a[1]').click()
    self.log("Logged in 1Control")
    time.sleep(2)

  def print_entity(self, entity, attribute, old, new, kwargs):
    try:
        self.log(f'Entity state change for {entity}. From: {old} to {new}')
        if new == 'on' and old == 'off':
          self.log('Pressing button on 1Control')

          if self.driver is None:
            self.log("Web driver not set > creating it now")
            options = webdriver.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('--headless')
            self.driver = webdriver.Chrome(options)
          else: 
            self.log("Web driver already set")

            wait = WebDriverWait(self.driver, 15)
            self.driver.get('https://web.1control.eu/web/en/#/device/' + self.onecontrol_device_id)
            if 'login' in self.driver.current_url:
                self.log("Not logged in 1Control > logging in now")
                self.driver.find_element(By.ID, 'userEmail').send_keys(self.onecontrol_email)
                self.driver.find_element(By.ID, 'userPassword').send_keys(self.onecontrol_password)
                self.driver.find_element(By.XPATH, '/html/body/app-root/div/main/app-login/section[2]/div/div/a[1]').click()
                wait.until_not(EC.visibility_of_element_located((By.CSS_SELECTOR, '.loading-loader-wrapper')))
                self.driver.get('https://web.1control.eu/web/en/#/device/' + self.onecontrol_device_id)
            else:
              self.log("Already logged in 1Control")
            self.log("Pressing button in 1Control")
            wait.until_not(EC.visibility_of_element_located((By.CSS_SELECTOR, '.loading-loader-wrapper')))
            wait.until(EC.visibility_of_element_located((By.ID, 'activateButton')))
            self.driver.find_element(By.ID, 'activateButton').click()
            wait.until(EC.visibility_of_element_located((By.ID, 'confirmButton')))
            self.driver.find_element(By.ID, 'confirmButton').click()
            time.sleep(2)
            self.log(f'Button pressed on 1Control')
            self.set_state('input_boolean.1control_gate_helper', state='off')
        else:
          self.log('New state not ON, skipping')
          return


    except Exception as e:
        print("An exception occurred")
        print(e)
