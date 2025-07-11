#!/usr/bin/env python3
"""
PDF 문서 재인덱싱 스크립트
"""

import os
import sys
from pathlib import Path

# 상대 경로 import를 위한 경로 설정
sys.path.append(str(Path(__file__).parent))

from services.search_service import SearchService
from services.pdf_processor import PDFProcessor

def main():
    print("🔄 PDF 문서 재인덱싱 시작...")
    
    # 환경 변수 설정 (이미 설정되어 있을 수 있음)
    if not os.getenv('ELASTICSEARCH_PASSWORD'):
        os.environ['ELASTICSEARCH_PASSWORD'] = "9uLLjRQt"
    
    # PDF 파일 경로 확인
    pdf_path = "../pdf/laws.pdf"
    
    if not Path(pdf_path).exists():
        print(f"❌ PDF 파일을 찾을 수 없습니다: {pdf_path}")
        return
    
    # PDF 정보 먼저 확인
    pdf_processor = PDFProcessor()
    pdf_info = pdf_processor.get_pdf_info(pdf_path)
    
    if "error" in pdf_info:
        print(f"❌ PDF 정보 조회 실패: {pdf_info['error']}")
        return
    
    print(f"📄 PDF 정보:")
    print(f"  - 파일명: {pdf_info['file_name']}")
    print(f"  - 총 페이지 수: {pdf_info['total_pages']}")
    print(f"  - 파일 크기: {pdf_info['file_size']:,} bytes")
    
    # 검색 서비스 초기화
    search_service = SearchService()
    
    # 기존 인덱스 삭제하고 재생성
    print("\n🗑️  기존 인덱스 삭제 중...")
    search_service.reset_index()
    
    # 새로운 인덱스 생성 및 문서 인덱싱
    print("📚 새로운 인덱스 생성 및 문서 인덱싱 중...")
    if search_service.initialize_index(pdf_path, recreate=True):
        print("✅ 인덱싱 완료!")
        
        # 통계 정보 출력
        stats = search_service.get_statistics()
        print(f"\n📊 인덱싱 결과:")
        print(f"  - 총 문서 수: {stats.get('total_documents', 0)}")
        
        if 'categories' in stats:
            print(f"  - 카테고리별 문서 수:")
            for category, count in stats['categories'].items():
                print(f"    * {category}: {count}개")
        
        # 간단한 검색 테스트
        print("\n🔍 검색 테스트:")
        test_queries = ["스토킹", "성폭력", "사행"]
        
        for query in test_queries:
            results = search_service.search(query, size=3)
            print(f"  - '{query}': {len(results)}개 결과")
            
            if results:
                for i, result in enumerate(results[:2], 1):
                    print(f"    [{i}] 페이지 {result.document.page_number}, 점수: {result.score:.2f}")
                    print(f"        {result.document.title[:50]}...")
        
    else:
        print("❌ 인덱싱 실패!")

if __name__ == "__main__":
    main() 