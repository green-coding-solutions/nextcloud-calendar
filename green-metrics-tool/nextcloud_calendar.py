import contextlib
import random
import string
import sys
import signal
import os

from playwright.sync_api import Playwright, sync_playwright, expect

from helpers.helper_functions import log_note, get_random_text, login_nextcloud, close_modal, timeout_handler, user_sleep

DOMAIN = os.environ.get('HOST_URL', 'http://app')

def run(playwright: Playwright, browser_name: str) -> None:
    log_note(f"Launch browser {browser_name}")
    if browser_name == "firefox":
        browser = playwright.firefox.launch(headless=False)
    else:
        browser = playwright.chromium.launch(headless=False, args=['--disable-gpu', '--disable-software-rasterizer', '--ozone-platform=wayland'])
    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()

    try:
        log_note("Opening login page")
        page.goto(f"{DOMAIN}/login")

        log_note("Logging in")
        login_nextcloud(page, domain=DOMAIN)
        user_sleep()

        # Wait for the modal to load. As it seems you can't close it while it is showing the opening animation.
        log_note("Close first-time run popup")
        close_modal(page)

        log_note("Going to calendar")
        page.get_by_role("link", name="Calendar", exact=True).click()
        user_sleep()

        #CREATE
        log_note("Create event")
        event_name = "Event " + ''.join(random.choices(string.ascii_letters, k=5))
        page.get_by_role("button", name="New event").click()
        page.get_by_placeholder("Event title").fill(event_name)
        page.get_by_role("button", name="Save").click()
        user_sleep()

        log_note("Checking if event was correctly saved")
        expect(page.get_by_text(event_name, exact=True)).to_be_visible()
        event_title_locator = page.locator(f'a.fc-event div.fc-event-title', has_text=event_name)
        expect(event_title_locator).to_have_count(1)
        user_sleep()

        # EDIT
        log_note("Modify event - Clicking edit form")
        page.get_by_text(event_name, exact=True).click()
        popover_locator = page.locator('div.event-popover')
        expect(popover_locator).to_be_visible()
        edit_button = popover_locator.locator('button:has-text("Edit")')
        edit_button.click()
        user_sleep()

        log_note('Typing in new detail text')
        title_input = popover_locator.locator('input[placeholder="Event title"]')
        expect(title_input).to_be_visible()
        expect(title_input).to_be_enabled()
        new_event_name = event_name + ''.join(random.choices(string.ascii_letters, k=5))
        title_input.fill(new_event_name)

        update_button = popover_locator.locator('button:has-text("Update")')
        update_button.click()
        user_sleep()

        log_note('Validating if new text was saved')
        updated_event_title_locator = page.locator(f'a.fc-event div.fc-event-title', has_text=new_event_name)
        expect(updated_event_title_locator).to_have_text(new_event_name)
        expect(updated_event_title_locator).to_have_count(1)
        user_sleep()


        # DELETE
        log_note("Delete the event - Opening delete popup")
        actions_button = popover_locator.locator('button[aria-label="Actions"]')
        expect(actions_button).to_be_visible()
        actions_button.click()

        actions_button_id = actions_button.get_attribute('id')
        menu_id = actions_button_id.replace('trigger-', '')
        menu_selector = f'ul#{menu_id}[role="menu"]'
        menu_locator = page.locator(menu_selector)
        expect(menu_locator).to_be_visible()
        user_sleep()

        log_note("Delete the event - Clicking delete")
        delete_button = menu_locator.locator('button.action-button:has-text("Delete")')
        expect(delete_button).to_be_visible()
        delete_button.click()

        log_note('Validating event was deleted')
        expect(updated_event_title_locator).to_have_count(0)
        user_sleep()

        page.close()
        log_note("Close browser")

    except Exception as e:
        if hasattr(e, 'message'): # only Playwright error class has this member
            log_note(f"Exception occurred: {e.message}")

        # set a timeout. Since the call to page.content() is blocking we need to defer it to the OS
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(20)
        #log_note(f"Page content was: {page.content()}")
        signal.alarm(0) # remove timeout signal

        raise e

    # ---------------------
    context.close()
    browser.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        browser_name = sys.argv[1].lower()
        if browser_name not in ["chromium", "firefox"]:
            print("Invalid browser name. Please choose either 'chromium' or 'firefox'.")
            sys.exit(1)
    else:
        browser_name = "firefox"

    with sync_playwright() as playwright:
        run(playwright, browser_name)
