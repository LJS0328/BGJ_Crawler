import time
from datetime import datetime, timedelta
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import json
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

#제품이 올라온 절대 시간 구하기(파싱시간 - 시간데이터)
def parse_relative_time(text):
    now = datetime.now()
    m = re.match(r"(\d+)(초|분|시간|일) 전", text)
    if not m:
        return "시간 형식 오류"
    value, unit = m.groups()
    delta = {"초": timedelta(seconds=int(value)),
             "분": timedelta(minutes=int(value)),
             "시간": timedelta(hours=int(value)),
             "일": timedelta(days=int(value))}[unit]
    return (now - delta).strftime("%Y-%m-%d %H:%M:%S")

def init_browser():
    opts = Options()
    opts.add_argument("--headless")  # 필요에 따라 주석 해제(화면 출력)
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=opts)
    driver.implicitly_wait(10)
    return driver

def get_soup(driver):
    return BeautifulSoup(driver.page_source, "html.parser")

def scrape_search_page(driver, base_url, page):
    url = f"{base_url}&order=score&page={page}"
    driver.get(url)
    time.sleep(2)
    soup = get_soup(driver)

    total_a_tags = 0
    ad_count = 0
    valid_links = set()

    for a in soup.select("a[href^='/products/']"):
        total_a_tags += 1

        # <a> 하위 텍스트 중 "AD"인 문자열이 있으면 광고
        if any(text == "AD" for text in a.stripped_strings):
            ad_count += 1
            continue

        href = a["href"].split("?")[0]
        valid_links.add("https://m.bunjang.co.kr" + href)

    logging.info(f"전체 a 태그: {total_a_tags}개, 광고: {ad_count}개, 파싱 데이터: {len(valid_links)}개")
    return list(valid_links)

# 상세 페이지 
def scrape_detail_page(driver, url):
   
    driver.get(url)
    time.sleep(1)
    soup = get_soup(driver)

    # 광고성(매입) 게시글 필터링
    desc = soup.select_one("div.ProductInfostyle__DescriptionContent-sc-ql55c8-3.eJCiaL")
    if desc and "매입" in desc.get_text():
        return None

    # 상품 상태(판매중/판매완료) 파싱
    status_img = soup.select_one("div.Productsstyle__ProductStatus-sc-13cvfvh-39 img")
    status = status_img["alt"].strip() if status_img else "판매중"
    
    # 게시글 제목 파싱 및 필터링
    title = soup.select_one("div.ProductSummarystyle__Name-sc-oxz0oy-3")
    title_text = title.get_text(strip=True) if title else "제목없음"
    
    if re.search(r"(매입|삽니다)", title_text):
        return None

    # 가격 정보 파싱
    price = soup.select_one("div.ProductSummarystyle__Price-sc-oxz0oy-5")
    price_text = price.get_text(strip=True) if price else "가격 정보 없음음"
    
    # 시간 데이터 파싱
    raw_time = "0초 전"
    for div in soup.select("div.ProductSummarystyle__Status-sc-oxz0oy-11"):
        txt = div.get_text(strip=True)
        if re.match(r"\d+(초|분|시간|일) 전", txt):
            if div.img:
                div.img.decompose()
            raw_time = txt
            break
    upload_time = parse_relative_time(raw_time)

    #데이터 파싱(제품 상태/배송비/직거래 지역 정보)
    condition = "제품 상태 정보 없음"
    delivery_fee = "배송비 정보 없음"
    direct_location = "직거래 지역 정보 없음"
    for div in soup.select("div.ProductSummarystyle__Value-sc-oxz0oy-21"):
        txt = div.get_text(strip=True)
        if re.search(r"\d+원$|무료", txt):
            delivery_fee = txt
        elif txt:
            direct_location = txt
        else:
            condition = txt

    #이미지 링크 파싱
    img = soup.find("img", src=lambda x: x and x.startswith("https://media.bunjang.co.kr/product/"))

    return {
        "title": title_text,
        "price": price_text,
        "condition": condition,
        "upload_time": upload_time,
        "delivery_fee": delivery_fee,
        "direct_location": direct_location,
        "url": url,
        "image_url": img["src"] if img else "",
        "status": status
    }

# 카테고리 페이지
def main():
    driver = init_browser()
    results = []

    subcategories = {
        "휴대폰": "https://m.bunjang.co.kr/categories/600700?req_ref=popular_category",
        "태블릿": "https://m.bunjang.co.kr/categories/600710?req_ref=popular_category",
        "웨어러블": "https://m.bunjang.co.kr/categories/600720?req_ref=popular_category",
        "오디오/영상": "https://m.bunjang.co.kr/categories/600500?req_ref=popular_category",
        "PC/노트북": "https://m.bunjang.co.kr/categories/600100?req_ref=popular_category",
        "PC부품/저장장치": "https://m.bunjang.co.kr/categories/600200?req_ref=popular_category",
    }

    pages = int(input("페이지 수 제한: "))
    for name, base_url in subcategories.items():
        logging.info(f"▶ 크롤링 시작 — {name}")
        for page in range(1, pages+1):
            links = scrape_search_page(driver, base_url, page)
            if not links:
                break
            for url in links:
                data = scrape_detail_page(driver, url)
                if data is None:
                    continue
                data["category"] = name
                data["platform"] = "번개장터"
                results.append(data)

    driver.quit()
    os.makedirs("./output", exist_ok=True)
    with open("./output/result.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

    print(f"크롤링 완료 → ./output/result.json (총 {len(results)}개)")

if __name__ == "__main__":
    main()
