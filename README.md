## Intro
This guide explains how to integrate 1Control Solo/Link with HomeAssistant by integrating 1Control web dashboard. This is not an official integration and it's not officially supported by 1Control, but something I've done to be able to control my 1Control solo from my HomeAssistant instance.

Since 1Control currently doesn't provide API or an HomeAssistant integration I'm using python/selenium to open the 1Control web dashboard and operate the Solo device.

## Requirements
- 1Control ****Solo + Link**** devices already set up on your 1Control app
- You must only have 1 gate se tup on your 1Control Solo (this could technically work even if you have more than 1 gate set up but it's not been tested)

## 1Control web dashboard setup
If you have the 1Control dashboard already set up and linked to your 1Control solo device you can skip this step

- Create an account on [https://web.1control.eu/](https://web.1control.eu/web/en/#/register)
- Make a note of your email and password, you'll need them later
- Once the account is created go to: https://web.1control.eu/web/en/#/dashboard
- Click on "Add" on the "Add device" section
- Click on Solo device
- Follow the guide to add a web user to your 1Control Solo device (IMPORTANT: you'll have to be close to your 1Control solo device to set it up for web control)
- Once done, refresh the dashboard page (https://web.1control.eu/web/en/#/dashboard) and make sure the 1Control device is there and can be operated from the dashboard
- Click on "Details" button on your 1Control device
- Make a note of the URL which contains the 1Control device id, you'll need it later (for instance: https://web.1control.eu/web/en/#/device/2410 has device id `2410`)

## HomeAssistant setup
- Go to your helpers page on HomeAssistant: https://my.home-assistant.io/redirect/helpers/
- Click on "Create helper"
- Create a switch (input boolean) helper and name it `1Control Gate Helper`
- Follow the guide to install AppDaemon on your HomeAssistant instance: https://github.com/hassio-addons/addon-appdaemon/blob/main/appdaemon/DOCS.md
- When AppDaemon is installed, open its configuration tab and:
  - Add the following to "System packages":
      - `chromium`
      - `chromium-chromedriver`
  - Add the following to "Python packages":
      - `selenium`
  - Add the following to "Init commands":
      - `echo "http://dl-cdn.alpinelinux.org/alpine/edge/community" > /etc/apk/repositories`
      - `echo "http://dl-cdn.alpinelinux.org/alpine/edge/main" >> /etc/apk/repositories`
      - `apk update`
- Start AppDaemon add-on and make sure no error are thrown in the logs tab
- Install Visual Studio Code add-on if you don't have it already (https://github.com/hassio-addons/addon-vscode)
- Open Visual Studio Code
- Press on the three horizontal lines icon (burger menu) on top left > File > Open Folder
- Insert `/addon_configs/a0d7b954_appdaemon/apps` in the text field and press OK
- Open `apps.yaml` file and add the following to the bottom of the file:
```yaml
 gate:
  module: gate
  class: GateBackend
```
- Create a new file in the same folder named  `gate.py` and paste the following (**IMPORTANT: make sure you update the config values highlighted with comments**)
```py
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
```
- Save the file
- Restart AppDaemon add-on
- Open AddDaemon logs tab and make sure you find these logs:
```
INFO gate: Logging into 1Control web
INFO gate: Logged in 1Control
```
- You're done! Try changing the state of your HomeAssistant helper and make sure the 1Control solo device is triggered. If everything works you should see logs such as:
```
INFO gate: Pressing button in 1Control
INFO gate: Button pressed on 1Control
```
- If you encounter issues you can create an issue on github and paste the AppDaemon logs

