#!/usr/bin/env python3

import argparse
import json
import os
import time
from re import search

import selenium
import selenium.webdriver.support.ui as ui
from appdirs import user_data_dir
from selenium import webdriver
# from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

gh_url = "https://canonical.greenhouse.io"
JOB_BOARD = "Canonical - Jobs"
# JOB_BOARD = "INTERNAL"

REGIONS = {
    "americas": [
        # United States
	"Home based - Americas, Albany",
        "Home based - Americas, Anchorage",
        "Home based - Americas, Atlanta",
        "Home based - Americas, Austin",
	"Home based - Amercias, Baltimore",
        "Home based - Americas, Boise",
        "Home based - Americas, Boston",
	"Home based - Americas, Buffalo",
        "Home based - Americas, Charlotte",
        "Home based - Americas, Chicago",
	"Home based - Americas, Cincinnati",
	"Home based - Americas, Cleveland",
        "Home based - Americas, Colorado",
        "Home based - Americas, Columbus",
        "Home based - Americas, Dallas",
	"Home based - Americas, Dayton",
	"Home based - Americas, Detroit",
        "Home based - Americas, Fresno",
        "Home based - Americas, Houston",
	"Home based - Americas, Honolulu",
	"Home based - Americas, Jacksonville, Florida",
	"Home based - Americas, Kansas City",
        "Home based - Americas, Las Vegas",
        "Home based - Americas, Los Angeles",
        "Home based - Americas, Miami",
	"Home based - Americas, Milwaukee",
	"Home based - Americas, Minneapolis",
	"Home based - Americas, Nashville, Tennessee",
        "Home based - Americas, New York",
	"Home based - Americas, Oklahoma City",
	"Home based - Americas, Omaha"
        "Home based - Americas, Philadelphia",
        "Home based - Americas, Phoenix",
        "Home based - Americas, Portland",
        "Home based - Americas, Raleigh",
	"Home based - Amercias, Rochester",
        "Home based - Americas, Sacramento",
        "Home based - Americas, Salt Lake City",
	"Home based - Americas, San Antonio",
	"Home based - Americas, San Bernadino, California",
        "Home based - Americas, San Diego, California",
        "Home based - Americas, San Francisco, California",
	"Home based - Americas, San Jose, California",
        "Home based - Americas, Seattle",
        "Home based - Americas, Spokane",
	"Home based - Americas, Syracuse",
        "Home based - Americas, Tacoma",
	"Home based - Americas, Tucson",
	"Home based - Americas, Tulsa",
        "Home based - Americas, Wichita",
	# Canada
        "Home based - Americas, Calgary",
        "Home based - Americas, Montreal",
        "Home based - Americas, Ottawa",
        "Home based - Americas, Toronto",
        "Home based - Americas, Vancouver",
        "Home based - Americas, Victoria",
        # South America
        "Home based - Americas, Buenos Aires",
        "Home based - Americas, Mexico City",
        "Home based - Americas, Montevideo",
        "Home based - Americas, Rio de Janeiro",
        "Home based - Americas, Santiago",
        "Home based - Americas, São Paulo",
    ],
    "eu": [
        "Home based - Europe, Amsterdam",
        "Home based - Europe, Barcelona",
        "Home based - Europe, Berlin",
        "Home based - Europe, Copenhagen",
        "Home based - Europe, Dublin",
        "Home based - Europe, Eindhoven",
        "Home based - Europe, Hamburg",
        "Home based - Europe, Helsinki",
        "Home based - Europe, Istanbul",
        "Home based - Europe, Munich",
        "Home based - Europe, Rotterdam",
        "Home based - Europe, Stockholm",
        "Home based - Europe, Stuttgart",
        "Home based - Europe, Gothenburg",
        "Home based - Europe, Malmö",
        "Home based - Europe, Uppsala",
        "Home based - Europe, Västerås",
        "Home based - Europe, Örebro",
        "Home based - Europe, Linköping",
        "Home based - Europe, Helsingborg",
        "Home based - Europe, Jönköping",
    ],
    "austin": [
        "Home based - Americas, Austin, Texas",
        "Home based - Americas, Bastrop, Texas",
        "Home based - Americas, Buda, Texas",
        "Home based - Americas, Fredricksberg, Texas",
        "Home based - Americas, San Marcos, Texas",
        "Home based - Americas, Dripping Springs, Texas",
        "Home based - Americas, Kyle, Texas",
        "Home based - Americas, Wimberly, Texas",
        "Home based - Americas, Lockhart, Texas"
    ],
    "brasil": [
        "Home based - Americas, Santiago",
        "Home based - Americas, Rio de Janeiro",
        "Home based - Americas, Belo Horizonte",
        "Home based - Americas, Porto Alegre",
        "Home based - Americas, Salvador",
        "Home based - Americas, Resife",
        "Home based - Americas, Fortaleza",
    ],
    "emea": [
        "Home based - Africa, Cairo",
        "Home based - Africa, Cape Town",
        "Home based - Africa, Lagos",
        "Home based - Africa, Nairobi",
        "Home based - Europe, Amsterdam",
        "Home based - Europe, Ankara",
        "Home based - Europe, Athens",
        "Home based - Europe, Barcelona",
        "Home based - Europe, Berlin",
        "Home based - Europe, Bratislava",
        "Home based - Europe, Brno",
        "Home based - Europe, Brussels",
        "Home based - Europe, Bucharest",
        "Home based - Europe, Budapest",
        "Home based - Europe, Cluj-Napoca",
        "Home based - Europe, Dublin",
        "Home based - Europe, Edinburgh",
        "Home based - Europe, Frankfurt",
        "Home based - Europe, Glasgow",
        "Home based - Europe, Helsinki",
        "Home based - Europe, Istanbul",
        "Home based - Europe, Kraków",
        "Home based - Europe, Lisbon",
        "Home based - Europe, Ljubljana",
        "Home based - Europe, Lyon",
        "Home based - Europe, Madrid",
        "Home based - Europe, Manchester",
        "Home based - Europe, Milan",
        "Home based - Europe, Moscow",
        "Home based - Europe, Munich",
        "Home based - Europe, Oslo",
        "Home based - Europe, Paris",
        "Home based - Europe, Plovdiv",
        "Home based - Europe, Prague",
        "Home based - Europe, Riga",
        "Home based - Europe, Rome",
        "Home based - Europe, Sofia",
        "Home based - Europe, St. Petersburg",
        "Home based - Europe, Stockholm",
        "Home based - Europe, Tallinn",
        "Home based - Europe, Timișoara",
        "Home based - Europe, Vienna",
        "Home based - Europe, Vilnius",
        "Home based - Europe, Warsaw",
        "Home based - Europe, Wrocław",
        "Home based - Europe, Zagreb",
    ],
    "apac": [
        "Home based - Asia Pacific, Adelaide",
        "Home based - Asia Pacific, Auckland",
        "Home based - Asia Pacific, Bangalore",
        "Home based - Asia Pacific, Brisbane",
        "Home based - Asia Pacific, Beijing",
        "Home based - Asia Pacific, Canberra",
        "Home based - Asia Pacific, Hong Kong",
        "Home based - Asia Pacific, Hyderabad",
        "Home based - Asia Pacific, Melbourne",
        "Home based - Asia Pacific, Seoul",
        "Home based - Asia Pacific, Shanghai",
        "Home based - Asia Pacific, Singapore",
        "Home based - Asia Pacific, Sydney",
        "Home based - Asia Pacific, Taipei",
        "Home based - Asia Pacific, Tokyo",
    ],
}

###############################################################
def parse_credentials():
    #print("Inside: parse_credentials()")

    # Read configuration from secured file in $HOME/.config/
    creds = os.path.join(user_data_dir("greenhouse"), "login.tokens")

    with open(os.path.expanduser(creds), "r") as auth:
        try:
            creds = json.load(auth)
            ghsso_user = creds["username"]
            ghsso_pass = creds["password"]
            return (ghsso_user, ghsso_pass)
        except FileNotFoundError:
            print("file {} does not exist".format(creds))


###############################################################
def sso_authenticate(browser, args):
    #print("Inside: sso_authenticate()")
    (ghsso_user, ghsso_pass) = parse_credentials()

    browser.get(gh_url)
    # click Accept Cookies button
    accept_cookies_btn = browser.find_elements_by_xpath('//*[@id="cookie-policy-button-accept"]')
    if accept_cookies_btn:
        accept_cookies_btn[0].click()

    # enter Ubuntu SSO email and password
    email_txt = browser.find_element_by_id("id_email")
    if email_txt:
        email_txt.send_keys(ghsso_user)

    password_txt = browser.find_element_by_id("id_password")
    if password_txt:
        password_txt.send_keys(ghsso_pass)

    continue_btn = browser.find_elements_by_xpath('//button[@name="continue"]')
    if continue_btn:
        continue_btn[0].click()

    # accept cookies so the popup doesn't obstruct clicks
    cookie_accept_btn = browser.find_elements_by_css_selector("#inform-cookies button")
    for btn in cookie_accept_btn:
        try:
            # click can raise if element exists but is in a hidden block
            btn.click()
        except selenium.common.exceptions.ElementNotInteractableException:
            pass

    # click "Got it" button for new tips
    got_it_btn = browser.find_elements_by_xpath('//a[text()="Got it"]')
    if got_it_btn:
        got_it_btn[0].click()

    # minimize trays so they don't obstruct clicks
    trays = browser.find_elements_by_xpath('//div[@data-provides="tray-close"]')
    for tray in trays:
        tray.click()

    if args.headless:
        mfa_token = input("Enter your 2FA token: ")
        time.sleep(0.2)
        mfa_txt = browser.find_element_by_xpath('//*[@id="id_oath_token"]')
        mfa_txt.send_keys(mfa_token)
        auth_button = browser.find_elements_by_xpath('//*[@id="login-form"]/button')[0].click()


###############################################################
def delete_posts(browser, wait, job_id):
    browser.get(f"{gh_url}/plans/{job_id}/jobapp")
    job_posts = len(wait.until(lambda browser: browser.find_elements_by_xpath('//*[@id="job_applications"]/tbody/tr')))

    for i in range(job_posts, 0, -1):
        browser.refresh()

        if i > 1:
            browser.find_element(By.CSS_SELECTOR,".job-application:nth-child(2) .unpublish-application-button",).click()
            browser.find_element(By.LINK_TEXT, "Unpublish").click()

            # Click options menu (Delete/Duplicate)
            browser.find_elements_by_xpath('//*[@id="job_applications"]/tbody/tr[2]/td[3]/div/div[1]')[0].click()
            print(f"Deleting post {i} from job {job_id} ...")
            browser.find_elements_by_xpath('//*[@id="job_applications"]/tbody/tr[2]/td[3]/div/div[2]/span/a')[0].click()
            browser.find_elements_by_xpath('//*[@id="confirm-delete-post"]')[0].click()
            time.sleep(0.2)


###############################################################
def parse_args():
    #print("Inside: parse_args()")
    parser = argparse.ArgumentParser(
        description="Duplicate Greenhouse job postings to multiple locations."
    )
    parser.add_argument(
        "job_ids",
        nargs="+",
        help="The numeric Greenhouse job id (the number in the URL when on the Job Dashboard)",
    )
    parser.add_argument(
        "--region",
        dest="regions",
        nargs="+",
        choices=["americas", "eu", "brasil", "austin", "emea", "apac"],
        help="The regions in which to create job postings",
    )
    parser.add_argument(
        "--browser",
        dest="browser",
        choices=["chrome", "firefox"],
        default="chrome",
        help="The browser to use (default is chrome)",
    )

    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete all posts under a given job_id"
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run the automation without the GUI"
    )

    parser.add_argument(
        "--limit",
        dest="limit",
        help="The specific job post to clone inside a REQ"
    )

    return parser.parse_args()


###############################################################
def main():
    args = parse_args()

    options = Options()

    prefs = {
        "profile.default_content_setting_values": {
            "plugins": 2,
            "popups": 2,
            "geolocation": 2,
            "notifications": 2,
            "fullscreen": 2,
            "ssl_cert_decisions": 2,
            "site_engagement": 2,
            "durable_storage": 2,
        }
    }

    if args.headless:
        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
    else:
        options.add_experimental_option("prefs", prefs)
        options.add_argument("disable-infobars")
        options.add_argument("--disable-extensions")

    if args.browser == "firefox":
        browser = webdriver.Firefox()
    else:
        browser = webdriver.Chrome(
            options=options
        )
    browser.maximize_window()

    sso_authenticate(browser, args)

    for job_id in args.job_ids:
        job_posts_page_url = f"{gh_url}/plans/{job_id}/jobapp"
        browser.get(job_posts_page_url)
        wait = ui.WebDriverWait(browser, 60) # timeout after 60 seconds

        if args.reset:
            print("[Disabled] The reset function must be updated to support multiple Canonical jobs.")
            #delete_posts(browser, wait, job_id)
            exit()

        multipage = False
        page = 1
        existing_ids = []
        existing_types = []
        existing_names = []
        existing_locations = []

        print(f"[Harvesting job details]")
        while True:
            print(f"-> Processing page {page}")
            time.sleep(1.5)

            # Ensure page navigation and job details have had sufficient time to load
            job_locations = wait.until(lambda browser: browser.find_elements_by_class_name("job-application__offices"))
            job_names = browser.find_elements_by_class_name("job-application__name")
            job_ids = browser.find_elements_by_class_name("job-edit-pencil")
            job_types = browser.find_elements_by_class_name("board-column")

            # harvest job details from each page of results
            existing_types += [result.text for result in job_types]
            existing_ids += [result.get_attribute("href").split("/")[4] for result in job_ids]
            existing_names += [result.text.split("\n")[0] for result in job_names]
            existing_locations += [result.text.strip("()") for result in job_locations]

            next_page = browser.find_elements_by_class_name("next_page")
            if not next_page:
                break

            if "disabled" not in next_page[0].get_attribute("class"):
                multipage = True
                page += 1
                next_page[0].click()
            else:
                break
 
        # return to first page of job posts
        if multipage:
            browser.get(job_posts_page_url)
            time.sleep(1.5)

        # Process updates for each `Canonical` job unless a limit arg is passed
        if args.limit:
            canonical_list = [args.limit]
        else:
            canonical_list = [existing_ids[i] for i,x in enumerate(existing_types) if "Canonical" == x or "INTERNAL" == x]

        for canonical_job_id in canonical_list:
            canonical_job_name = [existing_names[i] for i,x in enumerate(existing_ids) if canonical_job_id == x][0]
            limited_locations = [existing_locations[i] for i,x in enumerate(existing_names) if canonical_job_name in x]

            print(f"[Creating posts for \"{canonical_job_name}\"]")
            for region in args.regions:
                print(f"-> Processing {region}")
                region_locations = REGIONS[region]
                new_locations = set(region_locations) - set(limited_locations)

                if not new_locations:
                    print(f"--> All locations already exist.")
                    continue

                for location_text in sorted(new_locations):
                    print(f"--> Processing {location_text}")
                    publish_location_text = location_text.split(",")[-1].strip()

                    browser.get(f"{job_posts_page_url}s/new?from=duplicate&amp;greenhouse_job_application_id={canonical_job_id}")
                    time.sleep(2.5)

                    browser.refresh()
                    job_name_txt = browser.find_elements_by_xpath('//input[contains(@class, "Input__InputElem-ipbxf8-0")]')[0]

                    job_name = (job_name_txt.get_attribute("value").replace("Copy of ", "").strip())

                    job_name_txt.clear()
                    job_name_txt.send_keys(job_name)

                    post_to = browser.find_elements_by_xpath('//label[text()="Post To"]/..//input[1]')[0]
                    post_to.send_keys(JOB_BOARD)
                    post_to.send_keys(Keys.ENTER)

                    location = browser.find_elements_by_xpath('//label[text()="Location"]/..//input[1]')[0]
                    location.clear()
                    location.send_keys(location_text)

                    ## Publish the posts out to our external partner sites
                    try:
                        browser.find_elements_by_xpath('//label[text()="Glassdoor"]/input[1]')[0].click()
                    except:
                        print("INFO: Glassdoor board not available at the moment")

                    try:
                        browser.find_elements_by_xpath('//label[text()="Indeed"]/input[1]')[0].click()
                    except:
                        print("INFO: Indeed board not available at the moment")

                    publish_location = browser.find_elements_by_xpath('//input[@placeholder="Select location"]')[0]
                    publish_location.clear()
                    publish_location.send_keys(publish_location_text)
                    popup_menu_xpath = (
                        f'//ul[contains(@class, "ui-menu")]'
                        f'/li[contains(@class, "ui-menu-item")]'
                        f'/div[contains(text(), "{publish_location_text}")]'
                    )

                    location_choices = wait.until(
                        lambda browser: browser.find_elements_by_xpath(popup_menu_xpath)
                    )
                    publish_location.send_keys(Keys.DOWN)
                    publish_location.send_keys(Keys.TAB)
                    time.sleep(0.5)

                    # click the Save button
                    save_btn = browser.find_elements_by_xpath('//a[text()="Save"]')[0]
                    save_btn.click()

                    wait.until(lambda browser: browser.find_elements_by_class_name("job-application__offices"))

        print(f"[Marking all job posts live]")
        browser.get(job_posts_page_url)
        page = 1

        while True:
            print(f"-> Processing page {page}")
            time.sleep(1.5)

            # Ensure page navigation and job details have had sufficient time to load
            wait.until(lambda browser: browser.find_elements_by_class_name("job-application__offices"))
            
            ## Click the "Enable" button on each new post created, to make it live
            publish_btns = browser.find_elements_by_xpath('//tr[@class="job-application draft external"]//img[@class="publish-application-button"]')
            for btn in publish_btns:
                btn.click()
                time.sleep(0.5)

            next_page = browser.find_elements_by_class_name("next_page")
            if not next_page:
                break

            if "disabled" not in next_page[0].get_attribute("class"):
                next_page[0].click()
                page += 1
            else:
                break

    print("All done! Now go bring those candidates through to offers!")


if __name__ == "__main__":
    main()
