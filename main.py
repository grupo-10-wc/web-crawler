import pdb
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
import csv
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud

import requests as req
from pprint import pp
from bs4 import BeautifulSoup as bs
from pprint import pp
from analisador_lexico import tokenize, classify_tokens

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

def write_to_csv(token_counts: dict, good: list, bad: list, links: list, filename="output.csv"):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(['palavra', 'quantidade', 'classificação', 'link'])
        
        # Write "good" and "bad" tokens
        for link in links:
            for word, count in token_counts.items():
                classification = 'bom' if word in [x[0] for x in good] else 'ruim' if word in [x[0] for x in bad] else 'neutro'
                writer.writerow([word, count, classification, link])

def plot_wordcloud(good_tokens: list, bad_tokens: list):
    # Prepare text for word cloud
    good_words = ' '.join([token[0] for token in good_tokens])
    bad_words = ' '.join([token[0] for token in bad_tokens])

    # Create word clouds
    good_wordcloud = WordCloud(width=800, height=400, background_color="white").generate(good_words)
    bad_wordcloud = WordCloud(width=800, height=400, background_color="black", colormap="Reds").generate(bad_words)

    # Plot good word cloud
    plt.figure(figsize=(10, 5))
    plt.subplot(1, 2, 1)
    plt.imshow(good_wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.title("Palavras Positivas")

    # Plot bad word cloud
    plt.subplot(1, 2, 2)
    plt.imshow(bad_wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.title("Palavras Negativas")

    plt.tight_layout()
    plt.show()

def main():
    links = get_page_links(3)  # Assuming this function fetches the links
    article_links = []
    good_tokens = []
    bad_tokens = []
    token_counts = {}

    for link in links:
        print(f"Processando: {link}")
        text = get_page_content(link)
        if text:
            tokens = tokenize(text)
            token_count, good, bad = classify_tokens(tokens, link)
            token_counts.update(token_count)
            good_tokens.extend(good)
            bad_tokens.extend(bad)
            article_links.append(link)

    write_to_csv(token_counts, good_tokens, bad_tokens)

    plot_wordcloud(good_tokens, bad_tokens)



if __name__ == "__main__":
    main()
    