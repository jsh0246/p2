"""
검색 서비스
"""

import logging
from typing import List, Dict, Any, Optional

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from services.pdf_processor import PDFProcessor
from services.elasticsearch_client import ElasticsearchClient
from models.document import Document, SearchResult
from utils.text_utils import TextProcessor

logger = logging.getLogger(__name__)

class SearchService:
    """검색 서비스를 관리하는 메인 클래스"""
    
    def __init__(self):
        self.pdf_processor = PDFProcessor()
        self.es_client = ElasticsearchClient()
        self.text_processor = TextProcessor()
        
    def initialize_index(self, pdf_path: str, recreate: bool = False) -> bool:
        """PDF 파일을 인덱싱하여 검색 준비"""
        try:
            logger.info(f"인덱스 초기화 시작: {pdf_path}")
            
            # 인덱스 생성
            if not self.es_client.create_index(delete_existing=recreate):
                logger.error("인덱스 생성 실패")
                return False
            
            # 기존 문서가 있다면 재인덱싱 여부 확인
            if not recreate and self.es_client.get_document_count() > 0:
                logger.info("기존 인덱스에 문서가 있습니다. 재인덱싱을 원하면 recreate=True로 설정하세요.")
                return True
            
            # PDF 파일 처리
            logger.info("PDF 파일 처리 중...")
            documents = self.pdf_processor.extract_text_from_pdf(pdf_path)
            
            if not documents:
                logger.error("PDF에서 문서를 추출할 수 없습니다.")
                return False
            
            # 문서 인덱싱
            logger.info(f"{len(documents)}개 문서 인덱싱 중...")
            if self.es_client.bulk_index_documents(documents):
                logger.info("인덱싱 완료")
                return True
            else:
                logger.error("인덱싱 실패")
                return False
                
        except Exception as e:
            logger.error(f"인덱스 초기화 오류: {str(e)}")
            return False
    
    def search(self, query: str, size: int = 10, category: Optional[str] = None) -> List[SearchResult]:
        """키워드로 문서 검색"""
        try:
            logger.info(f"검색 시작: '{query}'")
            
            # 쿼리 전처리
            processed_query = self.text_processor.clean_text(query)
            
            if not processed_query:
                logger.warning("검색어가 비어있습니다.")
                return []
            
            # Elasticsearch 검색 실행
            search_results = self.es_client.search(
                query=processed_query,
                size=size,
                category=category
            )
            
            # 검색 결과 후처리
            processed_results = []
            for result in search_results:
                # 하이라이트 처리
                if result.highlights:
                    # 기존 하이라이트 사용
                    processed_results.append(result)
                else:
                    # 수동 하이라이트 생성
                    keywords = self.text_processor.extract_keywords(processed_query)
                    highlighted_content = self.text_processor.highlight_text(
                        result.document.content,
                        keywords,
                        max_length=300
                    )
                    
                    # 하이라이트 정보 추가
                    result.highlights = {
                        "content": [highlighted_content]
                    }
                    processed_results.append(result)
            
            logger.info(f"검색 완료: {len(processed_results)}개 결과")
            return processed_results
            
        except Exception as e:
            logger.error(f"검색 오류: {str(e)}")
            return []
    
    def search_by_category(self, category: str, size: int = 10) -> List[SearchResult]:
        """카테고리별 문서 검색"""
        try:
            logger.info(f"카테고리 검색: {category}")
            
            # 카테고리 검색은 match_all 쿼리 사용
            search_results = self.es_client.search(
                query="*",
                size=size,
                category=category
            )
            
            logger.info(f"카테고리 검색 완료: {len(search_results)}개 결과")
            return search_results
            
        except Exception as e:
            logger.error(f"카테고리 검색 오류: {str(e)}")
            return []
    
    def get_document_by_page(self, page_number: int, file_path: str) -> Optional[Document]:
        """페이지 번호로 특정 문서 조회"""
        try:
            if not self.es_client.client:
                return None
                
            # 파일 패스와 페이지 번호로 검색
            search_body = {
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"page_number": page_number}},
                            {"term": {"file_path": file_path}}
                        ]
                    }
                },
                "size": 1
            }
            
            response = self.es_client.client.search(
                index=self.es_client.index_name,
                body=search_body
            )
            
            if response['hits']['hits']:
                hit = response['hits']['hits'][0]
                return Document.from_dict(hit['_source'])
            
            return None
            
        except Exception as e:
            logger.error(f"문서 조회 오류: {str(e)}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """검색 인덱스 통계 정보"""
        try:
            stats = {
                "total_documents": self.es_client.get_document_count(),
                "elasticsearch_status": self.es_client.health_check(),
                "categories": self._get_category_stats()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"통계 조회 오류: {str(e)}")
            return {"error": str(e)}
    
    def _get_category_stats(self) -> Dict[str, int]:
        """카테고리별 문서 수 통계"""
        try:
            if not self.es_client.client:
                return {}
            
            # 카테고리별 집계 쿼리
            search_body = {
                "size": 0,
                "aggs": {
                    "categories": {
                        "terms": {
                            "field": "category",
                            "size": 10
                        }
                    }
                }
            }
            
            response = self.es_client.client.search(
                index=self.es_client.index_name,
                body=search_body
            )
            
            category_stats = {}
            if 'aggregations' in response and 'categories' in response['aggregations']:
                for bucket in response['aggregations']['categories']['buckets']:
                    category_stats[bucket['key']] = bucket['doc_count']
            
            return category_stats
            
        except Exception as e:
            logger.error(f"카테고리 통계 조회 오류: {str(e)}")
            return {}
    
    def suggest_queries(self, partial_query: str, size: int = 5) -> List[str]:
        """쿼리 자동완성 제안"""
        try:
            # 부분 쿼리로 검색하여 관련 키워드 추출
            search_results = self.search(partial_query, size=size*2)
            
            suggestions = set()
            for result in search_results:
                # 문서 내용에서 키워드 추출
                keywords = self.text_processor.extract_keywords(result.document.content)
                
                # 부분 쿼리와 유사한 키워드 찾기
                for keyword in keywords:
                    if partial_query.lower() in keyword.lower():
                        suggestions.add(keyword)
                        
                        if len(suggestions) >= size:
                            break
                
                if len(suggestions) >= size:
                    break
            
            return list(suggestions)[:size]
            
        except Exception as e:
            logger.error(f"쿼리 제안 오류: {str(e)}")
            return []
    
    def get_similar_documents(self, document_id: str, size: int = 5) -> List[SearchResult]:
        """유사 문서 찾기"""
        try:
            # 먼저 기준 문서 조회
            base_doc = self.get_document_by_page(int(document_id), "")
            
            if not base_doc:
                return []
            
            # 기준 문서의 주요 키워드 추출
            keywords = self.text_processor.extract_keywords(base_doc.content)
            
            # 주요 키워드로 유사 문서 검색
            if keywords:
                query = " ".join(keywords[:5])  # 상위 5개 키워드 사용
                return self.search(query, size=size)
            
            return []
            
        except Exception as e:
            logger.error(f"유사 문서 검색 오류: {str(e)}")
            return []
    
    def reset_index(self) -> bool:
        """인덱스 초기화"""
        try:
            return self.es_client.delete_index()
        except Exception as e:
            logger.error(f"인덱스 초기화 오류: {str(e)}")
            return False 