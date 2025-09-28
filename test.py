from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import os
import urllib.request
import time
import requests
from io import BytesIO

# --- KONFIGURASI ---
USERNAME = "username"
PASSWORD = "password"
TARGET = "citrabatik_pamekasan"

# --- INISIALISASI WEBDRIVER ---
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--disable-extensions")
options.add_argument("--disable-infobars")
options.add_argument("--lang=en-US,en")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

driver = webdriver.Chrome(options=options)

# --- CEK GAMBAR PERSEGI ---
def is_square(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, timeout=10, headers=headers)
        img = Image.open(BytesIO(response.content))
        return abs(img.width - img.height) <= 20
    except:
        return False

try:
    # --- LOGIN ---
    print("[INFO] Login ke Instagram...")
    driver.get("https://www.instagram.com/accounts/login/")
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, "username")))

    driver.find_element(By.NAME, "username").send_keys(USERNAME)
    driver.find_element(By.NAME, "password").send_keys(PASSWORD)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "svg[aria-label='Home'], svg[aria-label='Beranda']")))
    print("✅ Login berhasil!")
    time.sleep(3)

    # --- BUKA PROFIL TARGET ---
    print(f"[INFO] Mengakses profil @{TARGET}...")
    driver.get(f"https://www.instagram.com/{TARGET}/")
    time.sleep(5)

    # --- KUMPULKAN LINK POST ---
    post_links = set()
    for i in range(20):  # scroll 20x
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        links = driver.find_elements(By.TAG_NAME, 'a')
        for link in links:
            href = link.get_attribute('href')
            if href and '/p/' in href:
                post_links.add(href)
        print(f"[INFO] Scroll {i+1}/10 - Total post: {len(post_links)}")

    print(f"✅ Total {len(post_links)} post ditemukan")

    # --- DOWNLOAD GAMBAR ---
    count = 0
    processed = 0
    target_folder = './downloaded_images'
    os.makedirs(target_folder, exist_ok=True)
    print("[INFO] Mulai download...")

    for link in post_links:
        if count >= 50:
            break

        processed += 1
        print(f"[INFO] ({processed}/{len(post_links)}) Processing: {link}")
        driver.get(link)
        time.sleep(4)

        try:
            # Cari caption dengan selector yang lebih spesifik
            caption_selectors = [
                "span.x193iq5w.xeuugli.x13faqbe.x1vvkbs.xt0psk2.x1i0vuye.xvs91rp.xo1l8bm.x5n08af.x10wh9bi.xpm28yp.x8viiok.x1o7cslx.x126k92a",
                # "span[class*='x193iq5w'][class*='xeuugli']",
                # "._ap3a",
                # "h1._ap3a._aaco._aacu._aacx._aad7._aade"
            ]
            
            caption = ""
            caption_found = False
            
            for selector in caption_selectors:
                try:
                    caption_els = driver.find_elements(By.CSS_SELECTOR, selector)
                    print(f"[DEBUG] Selector '{selector}' menemukan {len(caption_els)} elemen")
                    
                    for el in caption_els:
                        text = el.text.strip()
                        if text and len(text) > len(caption):
                            caption = text
                            caption_found = True
                            print(f"[DEBUG] Caption ditemukan dengan selector: {selector}")
                    
                    if caption_found:
                        break
                except Exception as e:
                    print(f"[DEBUG] Error dengan selector {selector}: {e}")
                    continue
                    
        except Exception as e:
            print(f"[ERROR] Error saat mencari caption: {e}")
            caption = ""

        print(f"[DEBUG] Caption: {caption}")
        if not caption:
            print("[WARNING] Caption tidak ditemukan, skip.")
            continue
        elif "motif" not in caption.lower():  # Ubah ke case-insensitive
            print("[INFO] Tidak mengandung kata 'motif', skip.")
            continue

        # Ambil gambar dari div dengan class _aagv (ambil yang pertama)
        try:
            # Cari div dengan class _aagv
            aagv_divs = driver.find_elements(By.CSS_SELECTOR, "div._aagv")
            print(f"[DEBUG] Ditemukan {len(aagv_divs)} div dengan class '_aagv'")
            
            if not aagv_divs:
                print("[WARNING] Div '_aagv' tidak ditemukan, skip.")
                continue
                
            # Ambil gambar dari div pertama
            first_div = aagv_divs[0]
            img_element = first_div.find_element(By.TAG_NAME, "img")
            img_url = img_element.get_attribute("src")
            print(f"[DEBUG] Gambar ditemukan dari div '_aagv' pertama: {img_url[:100]}...")
            
        except Exception as e:
            print(f"[WARNING] Gambar tidak ditemukan di div '_aagv': {e}")
            # Fallback ke selector lama
            try:
                img_element = driver.find_element(By.CSS_SELECTOR, "article img[src*='scontent']")
                img_url = img_element.get_attribute("src")
                print("[DEBUG] Menggunakan fallback selector untuk gambar")
            except:
                print("[WARNING] Gambar tidak ditemukan dengan semua selector, skip.")
                continue

        if img_url and is_square(img_url):
            filename = f"motif_batik_{count+1:03d}.jpg"
            filepath = os.path.join(target_folder, filename)
            urllib.request.urlretrieve(img_url, filepath)
            count += 1
            print(f"✅ [{count}] Download berhasil: {filename}")
        else:
            print("[INFO] Gambar tidak persegi, skip.")

    print(f"🎉 Selesai! Total {count} gambar disimpan di '{target_folder}'")

finally:
    driver.quit()
