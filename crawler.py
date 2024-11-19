import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import json
import os

# 옵션 설정 (브라우저 창을 열지 않고 실행)
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# 요청 카운트 초기화
search_page_requests = 0
detail_page_requests = 0
total_requests = 0

# Selenium 구동
browser = webdriver.Chrome(options=chrome_options)
browser.implicitly_wait(10)

try:
    # 검색어 및 페이지 수 제한 입력
    itemname = input("검색 키워드 입력: ")
    try:
        max_pages = int(input("페이지 수 제한 입력 (숫자): "))
    except ValueError:
        print("올바른 숫자를 입력해주세요.")
        exit()

    # 검색 시작 시간 기록
    start_time = datetime.now()

    # 페이지 번호 초기화
    page = 1
    item_list_total = []

    while page <= max_pages:
        # 현재 페이지 URL 설정
        url = f"https://m.bunjang.co.kr/search/products?order=score&page={page}&q={itemname}"

        try:
            browser.get(url)
            search_page_requests += 1
            total_requests += 1
        except Exception as e:
            print(f"페이지 로딩 중 오류 발생: {e}")
            break

        # HTML 파싱
        time.sleep(2)  # 페이지 로딩 대기
        html = browser.page_source
        html_parser = BeautifulSoup(html, 'html.parser')

        # 모든 상품 이미지 태그 선택
        all_item_images = html_parser.find_all('img', src=lambda x: x and x.startswith('https://media.bunjang.co.kr/product/'))

        # '최근본상품' 섹션의 이미지를 수집
        recent_view_section = html_parser.find('div', string=lambda text: text and '최근본상품' in text)
        recent_view_images = set()
        if recent_view_section:
            recent_view_container = recent_view_section.find_parent('div')
            if recent_view_container:
                recent_images = recent_view_container.find_all('img', src=lambda x: x and x.startswith('https://media.bunjang.co.kr/product/'))
                recent_view_images = set(img['src'] for img in recent_images)

        # '최근본상품' 이미지를 제외한 상품 이미지 리스트 생성
        item_images = []
        for img in all_item_images:
            if img['src'] not in recent_view_images:
                item_images.append(img)

        # 디버깅: 현재 페이지와 아이템 수 출력
        print(f"페이지 {page}: {len(item_images)}개의 상품을 찾았습니다.")

        # 상품 이미지가 없으면 종료
        if not item_images:
            print("더 이상 상품이 없습니다. 크롤링을 종료합니다.")
            break

        # 현재 페이지의 상품 링크 추출
        item_list_current_page = []
        for img in item_images:
            # 이미지 부모 요소의 <a> 태그에서 링크를 추출
            parent_link = img.find_parent('a')
            if parent_link and parent_link['href'].startswith("/products/"):
                detail_url = f"https://m.bunjang.co.kr{parent_link['href']}"
                item_list_current_page.append(detail_url)
                item_list_total.append(detail_url)

        # 상세 페이지 로드 시도
        for detail_url in item_list_current_page:
            time.sleep(1)  # 지연 시간 추가

            for attempt in range(3):
                try:
                    browser.get(detail_url)
                    detail_page_requests += 1
                    total_requests += 1
                    time.sleep(1)  # 페이지 로딩 대기
                    break
                except Exception as e:
                    print(f"상세 페이지 로딩 중 오류 발생 (시도 {attempt + 1}/3): {e}")
                    time.sleep(2)
            else:
                print(f"{detail_url} 페이지를 로드할 수 없습니다. 다음 아이템으로 이동합니다.")
                continue

        # 다음 페이지로 이동
        page += 1

except Exception as e:
    print(f"예외 발생: {e}")
finally:
    # 파싱 종료 시간 기록
    end_time = datetime.now()

    # 결과 리스트 초기화
    output_data_list = []

    # 크롤링 결과가 없을 때 메시지 추가
    if not item_list_total:
        output_data_list.append({
            "message": "No items were found during crawling.",
            "total_items": 0,
            "search_keyword": itemname,
            "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration": str(end_time - start_time)
        })
    else:
        output_data = {
            "total_items": len(item_list_total),
            "search_page_requests": search_page_requests - 1,
            "detail_page_requests": detail_page_requests,
            "total_requests": total_requests,
            "search_keyword": itemname,
            "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration": str(end_time - start_time)
        }
        output_data_list.append(output_data)

    # JSON 파일 저장 경로 설정
    output_dir = "./output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_file = os.path.join(output_dir, "result.json")

    # JSON 파일로 저장
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data_list, f, ensure_ascii=False, indent=4)
        print(f"메타데이터가 '{output_file}' 파일로 저장되었습니다.")
    except Exception as e:
        print(f"JSON 파일 저장 중 오류 발생: {e}")

    # 브라우저 종료
    browser.quit()
