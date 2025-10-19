"""
Playwright UI Tests

End-to-end tests for the web interface using Playwright.
"""
import pytest
from playwright.sync_api import Page, expect
import os


@pytest.mark.ui
def test_test_runner_page_loads(page: Page):
    """Test that the test runner page loads correctly"""
    # Navigate to test runner
    page.goto("http://localhost:8000/test-runner")

    # Take screenshot of initial load
    page.screenshot(path="screenshots/test_runner_initial.png", full_page=True)

    # Check that the page title is correct
    expect(page).to_have_title("Test Runner - Saras Trading Platform")

    # Check for header
    header = page.locator("h1")
    expect(header).to_contain_text("Test Runner")

    # Check for stats cards
    stats_cards = page.locator(".stat-card")
    expect(stats_cards).to_have_count(4)

    # Take screenshot of loaded state
    page.screenshot(path="screenshots/test_runner_loaded.png", full_page=True)


@pytest.mark.ui
def test_test_runner_buttons_exist(page: Page):
    """Test that all test runner buttons are present"""
    page.goto("http://localhost:8000/test-runner")

    # Check for Run All Tests button
    run_all_btn = page.get_by_role("button", name="Run All Tests")
    expect(run_all_btn).to_be_visible()

    # Check for API Tests button
    api_btn = page.get_by_role("button", name="API Tests")
    expect(api_btn).to_be_visible()

    # Check for Auth Tests button
    auth_btn = page.get_by_role("button", name="Auth Tests")
    expect(auth_btn).to_be_visible()

    # Take screenshot
    page.screenshot(path="screenshots/test_runner_buttons.png", full_page=True)


@pytest.mark.ui
def test_api_documentation_loads(page: Page):
    """Test that API documentation page loads"""
    # Navigate to API docs
    page.goto("http://localhost:8000/docs")

    # Take screenshot
    page.screenshot(path="screenshots/api_docs_initial.png", full_page=True)

    # Check for Swagger UI
    expect(page.locator(".swagger-ui")).to_be_visible()

    # Take screenshot of full docs
    page.screenshot(path="screenshots/api_docs_loaded.png", full_page=True)


@pytest.mark.ui
@pytest.mark.integration
def test_stats_display(page: Page):
    """Test that statistics are displayed correctly"""
    page.goto("http://localhost:8000/test-runner")

    # Wait for stats to load (they are populated via JavaScript)
    page.wait_for_timeout(2000)

    # Check total runs stat
    total_runs = page.locator("#totalRuns")
    expect(total_runs).not_to_have_text("-")

    # Take screenshot of stats
    page.screenshot(path="screenshots/test_runner_stats.png", full_page=True)


@pytest.mark.ui
@pytest.mark.slow
def test_test_run_history_displays(page: Page):
    """Test that test run history is displayed"""
    page.goto("http://localhost:8000/test-runner")

    # Wait for test runs to load
    page.wait_for_timeout(3000)

    # Check for test runs list
    test_runs_list = page.locator("#testRunsList")
    expect(test_runs_list).to_be_visible()

    # Take screenshot
    page.screenshot(path="screenshots/test_runner_history.png", full_page=True)
