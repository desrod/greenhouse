#!/usr/bin/env python3

import argparse
import json
import os
import time
from textwrap import dedent

import psutil
import selenium
import selenium.webdriver.support.ui as ui
from appdirs import user_data_dir
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

gh_url = "https://canonical.greenhouse.io"
JOB_BOARD = "Canonical - Jobs"
JOB_BOARDS_PROTECTED = ["Canonical", "INTERNAL"]

# Read cities from external manifest
from cities import REGIONS


###############################################################
def clean_slate():
    for proc in psutil.process_iter():
        for browser_proc in ["geckodriver", "chromedriver"]:
            try:
                if browser_proc.lower() in proc.name().lower():
                    print(f"Stale PID {proc.pid} was found, terminating...")
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                print("Not found!")
                pass


###############################################################
def parse_credentials():
    # print("Inside: parse_credentials()")

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
    # print("Inside: sso_authenticate()")
    (ghsso_user, ghsso_pass) = parse_credentials()

    browser.get(gh_url)
    # click Accept Cookies button

    accept_cookies_btn = browser.find_elements(
        By.XPATH, '//*[@id="cookie-policy-button-accept"]'
    )
    if accept_cookies_btn:
        accept_cookies_btn[0].click()

    # enter Ubuntu SSO email and password
    email_txt = browser.find_element(By.ID, "id_email")
    if email_txt:
        email_txt.send_keys(ghsso_user)

    password_txt = browser.find_element(By.ID, "id_password")
    if password_txt:
        password_txt.send_keys(ghsso_pass)

    continue_btn = browser.find_elements(By.XPATH, '//button[@name="continue"]')
    if continue_btn:
        continue_btn[0].click()

    # accept cookies so the popup doesn't obstruct clicks
    cookie_accept_btn = browser.find_elements(By.CSS_SELECTOR, "#inform-cookies button")
    for btn in cookie_accept_btn:
        try:
            # click can raise if element exists but is in a hidden block
            btn.click()
        except selenium.common.exceptions.ElementNotInteractableException:
            pass

    # click "Got it" button for new tips
    got_it_btn = browser.find_elements(By.XPATH, '//a[text()="Got it"]')
    if got_it_btn:
        got_it_btn[0].click()

    # minimize trays so they don't obstruct clicks
    trays = browser.find_elements(By.XPATH, '//div[@data-provides="tray-close"]')
    for tray in trays:
        tray.click()

    if args.headless:
        mfa_token = input("Enter your 2FA token: ")
        time.sleep(0.2)
        mfa_txt = browser.find_element(By.XPATH, '//*[@id="id_oath_token"]')
        mfa_txt.send_keys(mfa_token)
        browser.find_elements(By.XPATH, '//*[@id="login-form"]/button')[0].click()


###############################################################
def parse_args():
    # print("Inside: parse_args()")
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
        choices=sorted(REGIONS.keys()),
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
        "--reset-all",
        action="store_true",
        help="Delete ALL posts under a given job_id (no --limit support)",
    )

    parser.add_argument(
        "--headless", action="store_true", help="Run the automation without the GUI"
    )

    parser.add_argument(
        "--limit", dest="limit", help="The specific job post to clone inside a REQ"
    )

    # arg parsing debug
    # print(vars(parser.parse_args()))
    return parser.parse_args()


###############################################################
def delete_posts(browser, wait, job_id):
    browser.get(f"{gh_url}/plans/{job_id}/jobapp")
    job_post_offset = 0
    while True:
        remove_tooltips(browser)
        browser.refresh()

        job_posts = len(
            wait.until(
                lambda browser: browser.find_elements(
                    By.XPATH, '//*[@id="job_applications"]/tbody/tr'
                )
            )
        )

        if job_posts == job_post_offset:
            break

        job_post = browser.find_element(
            By.XPATH,
            '//*[@id="job_applications"]/tbody/tr[' + str(job_post_offset + 1) + "]",
        )
        if job_post is None:
            break

        job_post_board = job_post.find_element(By.CSS_SELECTOR, ".board-column").text
        if job_post_board in JOB_BOARDS_PROTECTED:
            job_post_offset += 1
            continue

        if "live" in job_post.get_attribute("class").split():
            job_post_unpublish = job_post.find_element(
                By.CSS_SELECTOR, ".unpublish-application-button"
            )
            job_post_unpublish.click()
            browser.find_element(By.LINK_TEXT, "Unpublish").click()

        job_post_name = job_post.find_element(
            By.CSS_SELECTOR, ".job-application__name"
        ).text.replace("\n", " ")
        print(f"Deleting post '{job_post_name}' from job {job_id} ...")

        # Click options menu (Delete/Duplicate)
        job_post.find_element(By.XPATH, "td[3]/div/div[1]").click()
        job_post.find_element(By.XPATH, "td[3]/div/div[2]/span/a").click()
        browser.find_element(By.XPATH, '//*[@id="confirm-delete-post"]').click()
        time.sleep(0.2)


###############################################################
def remove_tooltips(browser):
    browser.execute_script(
        dedent(
            """
            const tooltipElements = document.getElementsByClassName("introjs-tooltiptext")
            if (tooltipElements.length) {
                const closeButton = tooltipElements[0].getElementsByClassName("close")[0]
                closeButton.click()
            }"""
        )
    )


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

    # Clean up any stale webdriver() processes from prior unexpected aborts
    clean_slate()
    if args.browser == "firefox":
        browser = webdriver.Firefox()
    else:
        browser = webdriver.Chrome(options=options)

    browser.maximize_window()

    sso_authenticate(browser, args)

    for job_id in args.job_ids:
        job_posts_page_url = f"{gh_url}/plans/{job_id}/jobapp"
        browser.get(job_posts_page_url)
        wait = ui.WebDriverWait(browser, 60)  # timeout after 60 seconds

        if args.reset_all:
            delete_posts(browser, wait, job_id)
            break

        multipage = False
        page = 1
        existing_ids = []
        existing_types = []
        existing_names = []
        existing_locations = []

        print("[Harvesting job details]")
        while True:
            print(f"-> Processing page {page}")
            time.sleep(3.5)
            remove_tooltips(browser)

            # Ensure page navigation and job details have had sufficient time to load
            job_locations = wait.until(
                lambda browser: browser.find_elements(
                    By.CLASS_NAME, "job-application__offices"
                )
            )
            job_names = browser.find_elements(By.CLASS_NAME, "job-application__name")
            job_ids = browser.find_elements(By.CLASS_NAME, "job-edit-pencil")
            job_types = browser.find_elements(By.CLASS_NAME, "board-column")

            # harvest job details from each page of results
            existing_types += [result.text for result in job_types]
            existing_ids += [
                result.get_attribute("href").split("/")[4] for result in job_ids
            ]
            existing_names += [result.text.split("\n")[0] for result in job_names]
            existing_locations += [result.text.strip("()") for result in job_locations]

            next_page = browser.find_elements(By.CLASS_NAME, "next_page")
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
            time.sleep(3.5)

        # Process updates for each `Canonical` job unless a limit arg is passed
        if args.limit:
            canonical_list = [args.limit]
        else:
            canonical_list = [
                existing_ids[i]
                for i, x in enumerate(existing_types)
                if x in JOB_BOARDS_PROTECTED
            ]

        for canonical_job_id in canonical_list:
            canonical_job_name = [
                existing_names[i]
                for i, x in enumerate(existing_ids)
                if canonical_job_id == x
            ][0]
            limited_locations = [
                existing_locations[i]
                for i, x in enumerate(existing_names)
                if canonical_job_name in x
            ]

            print(f'[Creating posts for "{canonical_job_name}"]')
            for region in args.regions:
                print(f"-> Processing {region}")
                region_locations = REGIONS[region]
                new_locations = set(region_locations) - set(limited_locations)

                if not new_locations:
                    print("--> All locations already exist.")
                    continue

                for location_text in sorted(new_locations):
                    print(f"--> Processing {location_text}")
                    publish_location_text = location_text.split(",", 1)[-1].strip()

                    browser.get(
                        f"{job_posts_page_url}s/new?from=duplicate&amp;greenhouse_job_application_id={canonical_job_id}"
                    )
                    time.sleep(3.5)
                    remove_tooltips(browser)

                    browser.refresh()
                    job_name_txt = browser.find_elements(
                        By.XPATH,
                        '//input[contains(@class, "Input__InputElem-sc-ipbxf8-0")]',
                    )[0]
                    job_name = (
                        job_name_txt.get_attribute("value")
                        .replace("Copy of ", "")
                        .strip()
                    )

                    job_name_txt.clear()
                    job_name_txt.send_keys(job_name)

                    post_to = browser.find_elements(
                        By.XPATH, '//label[text()="Post To"]/..//input[1]'
                    )[0]
                    post_to.send_keys(JOB_BOARD)
                    post_to.send_keys(Keys.ENTER)

                    location = browser.find_elements(
                        By.XPATH, '//label[text()="Location"]/..//input[1]'
                    )[0]
                    location.clear()
                    location.send_keys(location_text)

                    ## Publish the posts out to our external partner sites
                    # try:
                    #     browser.find_elements(By.XPATH, '//label[text()="Glassdoor"]/input[1]')[0].click()
                    # except:
                    #     print("INFO: Glassdoor board not available at the moment")

                    try:
                        browser.find_elements(
                            By.XPATH, '//label[text()="Indeed"]/input[1]'
                        )[0].click()
                    except:
                        print("INFO: Indeed board not available at the moment")

                    publish_location = browser.find_elements(
                        By.XPATH, '//input[@placeholder="Select location"]'
                    )[0]
                    publish_location.clear()
                    publish_location.send_keys(publish_location_text)
                    popup_menu_xpath = (
                        f'//ul[contains(@class, "ui-menu")]'
                        f'/li[contains(@class, "ui-menu-item")]'
                        f'/div[contains(text(), "{publish_location_text}")]'
                    )
                    wait.until(
                        lambda browser: browser.find_elements(
                            By.XPATH, popup_menu_xpath
                        )
                    )
                    publish_location.send_keys(Keys.DOWN)
                    publish_location.send_keys(Keys.TAB)

                    browser.find_elements(
                        By.XPATH, '//label[text()="Remote"]/input[1]'
                    )[0].click()
                    time.sleep(0.5)

                    # click the Save button
                    save_btn = browser.find_elements(By.XPATH, '//a[text()="Save"]')[0]
                    save_btn.click()

                    wait.until(
                        lambda browser: browser.find_elements(
                            By.CLASS_NAME, "job-application__offices"
                        )
                    )

        print("[Marking all job posts live]")
        browser.get(job_posts_page_url)
        page = 1

        while True:
            print(f"-> Processing page {page}")
            time.sleep(3.5)

            # Ensure page navigation and job details have had sufficient time to load
            wait.until(
                lambda browser: browser.find_elements(
                    By.CLASS_NAME, "job-application__offices"
                )
            )

            ## Click the "Enable" button on each new post created, to make it live
            publish_btns = browser.find_elements(
                By.XPATH,
                '//tr[@class="job-application draft external"]//img[@class="publish-application-button"]',
            )
            for btn in publish_btns:
                btn.click()
                time.sleep(0.5)

            next_page = browser.find_elements(By.CLASS_NAME, "next_page")
            if not next_page:
                break

            if "disabled" not in next_page[0].get_attribute("class"):
                next_page[0].click()
                page += 1
            else:
                break

    print("All done! Now go bring those candidates through to offers!")
    browser.quit()

if __name__ == "__main__":
    main()
