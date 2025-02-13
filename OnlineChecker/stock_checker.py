import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import threading
import tkinter as tk
from tkinter import messagebox

# Hardcoded list of URLs to check
urls = [
    "https://www.target.com/p/pokemon-trading-card-game-sword-38-shield-astral-radiance-elite-trainer-box/-/A-86093593#lnk=sametab",
    "https://www.target.com/p/pokemon-trading-card-game-sword-38-shield-8212-brilliant-stars-elite-trainer-box/-/A-84713762#lnk=sametab"
]

# Flag to stop checking when "In Stock" is found
stop_monitoring = False

def create_image(color):
    """Create an image for the tray icon."""
    width = 64
    height = 64
    image = Image.new("RGB", (width, height), color)
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 0, width, height], fill=color)
    return image

def show_notification(status):
    """Function to display a notification in the system tray."""
    icon.icon = create_image("green" if status == "In Stock" else "red")
    icon.visible = True
    time.sleep(5)  # Show notification for 5 seconds
    # We don't reset the icon to red here. The green icon stays visible until manually quit

def show_popup():
    """Function to show a pop-up window when the item is in stock."""
    root = tk.Tk()
    root.title("Item In Stock")
    root.geometry("300x100")
    label = tk.Label(root, text="Item is In Stock!", font=("Arial", 14))
    label.pack(pady=20)
    button = tk.Button(root, text="OK", command=root.destroy)
    button.pack(pady=5)
    root.mainloop()

def check_stock(driver, url):
    """Checks if the text 'Out of stock' exists on the webpage using Selenium."""
    global stop_monitoring
    try:
        # Open the URL in a new tab
        driver.execute_script("window.open('');")  # Open a new tab
        driver.switch_to.window(driver.window_handles[-1])  # Switch to the new tab
        driver.get(url)

        # Wait for the body element to be present (ensuring the page is loaded)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Explicit wait to ensure the page content (including dynamic elements) has loaded
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Out of stock')]")) # this is the text it is checking for
        )

        # Get the page source (entire HTML content of the page)
        page_source = driver.page_source

        # Check if the text 'Out of stock' exists in the page source
        if "Out of stock" in page_source:
            result = "Out of Stock"
        else:
            result = "In Stock"
            stop_monitoring = True  # Stop monitoring once item is in stock

        # Close the tab after checking the URL
        driver.close()
        # Switch back to the original tab
        driver.switch_to.window(driver.window_handles[0])

        return result

    except Exception as e:
        driver.quit()  # Ensure the driver quits in case of error
        return f"Error: {e}"

def monitor_stock(driver):
    """Periodically checks the stock status of all URLs."""
    global stop_monitoring
    while not stop_monitoring:
        print("\nChecking stock status...")
        for url in urls:
            if stop_monitoring:
                break
            status = check_stock(driver, url)
            print(f"{url}: {status}")
            if status == "In Stock":
                show_notification(status)  # Show tray notification
                show_popup()  # Show a pop-up
                return  # Stop further checks and keep the icon visible
        print("\nWaiting for 30 seconds...\n")
        if not stop_monitoring:
            time.sleep(30)

def on_quit(icon, item):
    """Handles the quit action for the system tray icon."""
    icon.stop()

# Set up the system tray icon
icon = pystray.Icon("Stock Monitor", create_image("red"), menu=pystray.Menu(item('Quit', on_quit)))

# Set up Chrome options
chrome_options = Options()
chrome_options.add_argument("--disable-gpu")  # Disable GPU hardware acceleration
chrome_options.add_argument("--disable-software-rasterizer")  # Disable software fallback for GPU
chrome_options.add_argument("--enable-unsafe-swiftshader")  # Allow software rendering fallback
chrome_options.add_argument("--disable-webgl")  # Disable WebGL entirely
chrome_options.add_argument("--no-sandbox")  # Necessary for some environments
chrome_options.add_argument("--disable-dev-shm-usage")  # Disable /dev/shm usage, useful in some environments

# Path to the ChromeDriver
driver_path = "./chromedriver.exe"  # Ensure this path is correct
service = Service(driver_path)

# Initialize the WebDriver once
driver = webdriver.Chrome(service=service, options=chrome_options)

# Open the initial URL to load the browser window
driver.get("about:blank")  # Open a blank page initially

# Set the window size and position (adjust it as per your preference)
driver.set_window_size(800, 600)  # Example: Set to 800x600 or any size you prefer
driver.set_window_position(100, 100)  # Example: Set to position (100, 100)

# Run the stock monitoring in a separate thread to allow tray icon to run concurrently
monitor_thread = threading.Thread(target=monitor_stock, args=(driver,))
monitor_thread.daemon = True
monitor_thread.start()

# Start the tray icon
icon.run()
