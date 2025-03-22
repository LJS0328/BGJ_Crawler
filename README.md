# 🚀 번개장터 크롤러

Python + Selenium 기반으로 번개장터 상품을 자동 크롤링하고, 결과를 JSON/CSV로 저장합니다.

---

## 📦 Requirements

- Python 3.8+
- Chrome (버전 호환되는 ChromeDriver)
- Docker & Docker Compose (선택)

```bash
pip install -r requirements.txt
```

---

## ⚙️ 로컬 실행

1️⃣ 크롤링

```bash
python crawler.py
```
크롤러 실행시 페이지 수 제한을 입력 받음

페이지 수 제한: 각 카테고리당 순회할 최대 페이지 수

결과 → ./output/result.json

