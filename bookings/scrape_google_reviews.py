import time
import json
import os
import sys
import mysql.connector
from django.core.management.base import BaseCommand
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class Command(BaseCommand):
    help = "Scrape Google reviews and save to DB + JSON"

    def handle(self, *args, **kwargs):

        DB = {
            "host": "localhost",
            "user": "root",
            "password": "",
            "database": "klickit_booking",
        }

        urls = {
            "itechie_google_maps" : "https://www.google.com/maps/place/iTechie+(Intuition+Technology)+-+Authorised+Laptop+%26+Desktop+Service+Center./@19.0147246,72.8265977,15z/data=!4m12!1m2!2m1!1sComputer+repair+service!3m8!1s0x3be7cf36d4f4c081:0x1021bf580f7316a4!8m2!3d19.0146945!4d72.836876!9m1!1b1!15sChdDb21wdXRlciByZXBhaXIgc2VydmljZVoZIhdjb21wdXRlciByZXBhaXIgc2VydmljZZIBF2NvbXB1dGVyX3JlcGFpcl9zZXJ2aWNlqgFyCggvbS8wMW0zdgoJL20vMGNwbHp0EAEqGyIXY29tcHV0ZXIgcmVwYWlyIHNlcnZpY2UoADIfEAEiG5ZPRRzKTohRmgOq9ZhkEWLdI6DXsZEak92KdDIbEAIiF2NvbXB1dGVyIHJlcGFpciBzZXJ2aWNl4AEA!16s%2Fg%2F11ww72w107?entry=ttu&g_ep=EgoyMDI1MDkyMS4wIKXMDSoASAFQAw%3D%3D",
            "klickit_google_maps" : "https://www.google.com/maps/place/KlickIT+Solutions+%26+Services/@19.0197377,72.8423833,17z/data=!4m9!3m8!1s0x3be7b71dce9f04e3:0x250d70c6cfa8284b!8m2!3d19.1408988!4d72.8333809!9m1!1b1!10e5!16s%2Fg%2F11t1q89nqx?entry=ttu&g_ep=EgoyMDI1MDkyMi4wIKXMDSoASAFQAw%3D%3D"
        }

        table_map = {
            "itechie_google_maps": "google_reviews_itechie",
            "klickit_google_maps": "google_reviews_klickit",
        }

        # ---- DB CONNECTION ----
        conn = mysql.connector.connect(**DB)
        cursor = conn.cursor()

        # ---- CREATE TABLES IF NOT EXISTS ----
        for table in table_map.values():
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS `{table}` (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    reviewer_name VARCHAR(255),
                    review TEXT,
                    rating TINYINT,
                    image VARCHAR(1024),
                    inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY uniq_review (reviewer_name(150), review(255))
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)

        conn.commit()
        self.stdout.write("✔ Tables ensured")

        # ---- SELENIUM SETUP ----
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--window-size=1920,1080")

        driver = webdriver.Chrome(options=chrome_options)

        all_reviews = {}

        for key, url in urls.items():

            self.stdout.write(f"\n🔍 Processing: {key}")
            driver.get(url)
            time.sleep(8)

            # ---- Accept Cookies ----
            try:
                btn = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, '//button[contains(., "Accept") or contains(., "agree") or contains(., "I agree")]')
                    )
                )
                btn.click()
            except:
                pass

            # ---- Open Reviews Tab ----
            try:
                review_tab = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, '//button[contains(@aria-label,"Reviews") or contains(text(),"Reviews")]')
                    )
                )
                review_tab.click()
                time.sleep(4)
            except Exception as e:
                self.stdout.write("❌ Review tab open error")
                continue

            # ---- Scroll reviews ----
            try:
                scrollable = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//div[contains(@class, "m6QErb")]')
                    )
                )
                last_height = driver.execute_script('return arguments[0].scrollHeight;', scrollable)
                same = 0

                while same < 6:
                    driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight;', scrollable)
                    time.sleep(3)
                    new_height = driver.execute_script('return arguments[0].scrollHeight;', scrollable)

                    if new_height == last_height:
                        same += 1
                    else:
                        same = 0

                    last_height = new_height

            except:
                self.stdout.write("❌ Scroll failed")
                continue

            # ---- Extract Review Blocks ----
            try:
                blocks = driver.find_elements(By.XPATH, '//div[@data-review-id]')
            except:
                blocks = []

            self.stdout.write(f"➡ Found {len(blocks)} review blocks")

            collected = []
            seen = set()

            for block in blocks:
                try:
                    name = block.find_element(By.XPATH, './/div[contains(@class,"d4r55")]').text.strip()
                    review = block.find_element(By.XPATH, './/span[contains(@class,"wiI7pd")]').text.strip()

                    rating_el = block.find_element(By.XPATH, './/span[contains(@aria-label,"star")]')
                    rating = int(rating_el.get_attribute("aria-label").split(" ")[0])

                    try:
                        img = block.find_element(By.XPATH, './/img[contains(@src,"googleusercontent")]').get_attribute("src")
                    except:
                        img = ""

                    key_pair = (name.lower(), review.lower())
                    if key_pair not in seen:
                        seen.add(key_pair)
                        collected.append({
                            "name": name,
                            "review": review,
                            "rating": rating,
                            "image": img
                        })

                except:
                    continue

            self.stdout.write(f"✔ Collected {len(collected)} unique reviews")

            # ---- Insert into DB ----
            table = table_map[key]

            sql = f"""
                INSERT INTO `{table}` (reviewer_name, review, rating, image)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE inserted_at = CURRENT_TIMESTAMP
            """

            inserted = 0
            for r in collected:
                cursor.execute(sql, (r['name'], r['review'], r['rating'], r['image']))
                inserted += 1

            conn.commit()
            self.stdout.write(f"✔ Inserted {inserted} reviews → {table}")

            all_reviews[key] = collected

        driver.quit()

        # ---- Save JSON Files ----
        base_path = "reviews_json"
        if not os.path.isdir(base_path):
            os.makedirs(base_path, exist_ok=True)

        combined_reviews = {}

        for src, reviews in all_reviews.items():
            file = os.path.join(base_path, f"reviews_{src}.json")

            old = []
            if os.path.exists(file):
                old = json.load(open(file)).get("data", [])

            final = old + [r for r in reviews if not any(
                (r['name'].lower() == o['name'].lower() and r['review'].lower() == o['review'].lower())
                for o in old
            )]

            json.dump({"data": final}, open(file, "w"), indent=4)

            for f in final:
                combined_reviews[f"{f['name']}||{f['review']}"] = f

        json.dump(
            {"data": list(combined_reviews.values())},
            open(os.path.join(base_path, "reviews_combined.json"), "w"),
            indent=4
        )

        self.stdout.write("\n🎉 Google Reviews Scraping Completed Successfully!")
