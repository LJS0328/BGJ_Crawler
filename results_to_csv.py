# -*- coding: utf-8 -*-

import json
import csv
import io
import os

def process_results(json_path="result.json", output_csv="sorted_results.csv"):
    # 현재 작업 디렉토리 출력
    current_directory = os.getcwd()
    print(f"현재 작업 디렉토리: {current_directory}")
    
    # output 디렉토리 경로 설정
    output_dir = os.path.join(current_directory, "output")
    
    # output 디렉토리가 없으면 생성
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # JSON 파일 전체 경로 설정
    full_json_path = os.path.join(output_dir, json_path)
    if not os.path.exists(full_json_path):
        print(f"[ERROR] JSON 파일 '{full_json_path}'을(를) 찾을 수 없습니다.")
        return
    
    # JSON 파일 로드
    with io.open(full_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 단일 객체인 경우 리스트로 변환
    if isinstance(data, dict):
        data = [data]
    
    # CSV 파일 전체 경로 설정
    full_csv_path = os.path.join(output_dir, output_csv)
    
    # CSV 파일로 저장 (UTF-8 BOM 추가)
    with open(full_csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ["search_keyword", "total_items", "search_page_requests", "detail_page_requests", "start_time", "end_time", "duration", "total_requests"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in data:
            writer.writerow(row)
    
    print(f"[INFO] CSV 파일 '{full_csv_path}'로 저장 완료.")

    # CSV 파일 내용을 출력
    print("[INFO] 저장된 CSV 파일 내용:")
    with open(full_csv_path, 'r', encoding='utf-8-sig') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            print(row)

if __name__ == "__main__":
    process_results()
