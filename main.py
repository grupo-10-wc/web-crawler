import pdb
import boto3
import os 
import csv
import pandas as pd
import matplotlib.pyplot as plt
import requests as req

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from wordcloud import WordCloud
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
    for i in range(qtd_paginas):
        res = req.get("https://g1.globo.com/busca/", {"q":"conta+de+energia", "page":i+1})
        soup = bs(res.text)
        
        cards = soup.find_all(class_="widget widget--card widget--info")
        cards = [card for card in cards if "globoplay" not in str(card)]
        
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
    plt.figure(figsize=(10, 10))
    plt.subplot(10, 10, 1)
    plt.imshow(good_wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.title("Palavras Positivas")

    # Plot bad word cloud
    plt.subplot(10, 10, 2)
    plt.imshow(bad_wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.title("Palavras Negativas")

    plt.tight_layout()
    plt.show()
    
def send_s3(local_filename: str, bucket_name: str, object_name: str):
    
    load_dotenv()
    
    sesssion = boto3.Session(
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.getenv('AWS_SESSION_TOKEN'),
    )
    
    s3 = sesssion.client('s3')
    
    try:
        s3.upload_file(local_filename, bucket_name, object_name)
        print(f"Arquivo enviada para s3://{bucket_name}/{object_name}")
    except Exception as e:
        print(f"Erro ao enviar para o S3: {e}") 

def save_wordcloud(
    good_tokens: list,
    bad_tokens: list,
    local_filename: str
):
    good_words = ' '.join([token[0] for token in good_tokens])
    bad_words = ' '.join([token[0] for token in bad_tokens])

    good_wordcloud = WordCloud(width=800, height=400, background_color="white").generate(good_words)
    bad_wordcloud = WordCloud(width=800, height=400, background_color="black", colormap="Reds").generate(bad_words)

    plt.figure(figsize=(16, 8))
    plt.subplot(1, 2, 1)
    plt.imshow(good_wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.title("Palavras Positivas")

    plt.subplot(1, 2, 2)
    plt.imshow(bad_wordcloud, interpolation="bilinear")
    plt.axis("off")
    plt.title("Palavras Negativas")

    plt.tight_layout()

    plt.savefig(local_filename, dpi=300)
    plt.close()

    print(f"Imagem salva localmente como {local_filename}")   

def save_text_to_cache(texts: list, filename: str = "cache.txt"):
    with open(filename, 'w', encoding='utf-8') as file:
        for text in texts:
            if text:
                file.write(text + "\n\n" + "="*50 + "\n\n")
    print(f"Textos salvos em {filename}")

def load_text_from_cache(filename: str = "cache.txt") -> str:
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        return None

def main():
    cache_filename = "cache.txt"
    
    cached_text = load_text_from_cache(cache_filename)
    
    if cached_text:
        print("Usando txt cache")
        tokens = tokenize(cached_text)
        token_count, good, bad = classify_tokens(tokens, "cached_data")
        good_tokens = good
        bad_tokens = bad
    else:
        print("Realizando scrapping")
        links = get_page_links(100)
        article_links = []
        good_tokens = []
        bad_tokens = []
        token_counts = {}
        scraped_texts = []

        for link in links:
            print(f"Processando: {link}")
            text = get_page_content(link)
            if text:
                scraped_texts.append(text)
                tokens = tokenize(text)
                token_count, good, bad = classify_tokens(tokens, link)
                token_counts.update(token_count)
                good_tokens.extend(good)
                bad_tokens.extend(bad)
                article_links.append(link)

        save_text_to_cache(scraped_texts, cache_filename)
        
        write_to_csv(token_counts, good_tokens, bad_tokens, article_links)

    save_wordcloud(good_tokens, bad_tokens, 'wordcloud_imagem.png')
    send_s3(
        local_filename='wordcloud_imagem.png',
        bucket_name='s3-trusted-bucket-wc-gabriel',
        object_name='wordcloud_imagem.png'
    )
    
    if not cached_text:  # Only upload CSV if we scraped new data
        send_s3(
            local_filename='output.csv',
            bucket_name='s3-trusted-bucket-wc-gabriel',
            object_name='output.csv'
        )


if __name__ == "__main__":
    main()