import pdb
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC

import requests as req
from pprint import pp
from bs4 import BeautifulSoup as bs
from pprint import pp


def initialize_driver() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.page_load_strategy = "eager"
    options.add_experimental_option("prefs", {
    "safebrowsing.enabled": True
})
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    
def burlar_bloqueador(driver: webdriver.Chrome, url:str) -> None:
    driver.get(url)
    
    try:
        text = driver.find_element(By.CLASS_NAME, "mc-article-body").text
        return text
    except:
        print(f"article not found {url}")
    
def get_page_links(qtd_paginas:int):
    links = []
    for i in range(1, qtd_paginas+1):
        res = req.get("https://g1.globo.com/busca/", {"q":"energia", "page":i})
        soup = bs(res.text)
        
        cards = soup.find_all(class_="widget widget--card widget--info")
        cards = [card for card in cards if "video" not in str(card)]
        for card in cards:
            links.append(card.find("a")["href"].replace("//", "https://"))
    return links


def get_page_content(url:str):
    driver = initialize_driver()
    text = burlar_bloqueador(driver, url)
    return text

def main():

    links = get_page_links(10)
    for link in links:
        print(get_page_content(link))
    
    return None

if __name__ == "__main__":
    main()
    