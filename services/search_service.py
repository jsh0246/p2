"""
검색 서비스 - Elasticsearch Text Analysis 개선 버전
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
    """검색 서비스를 관리하는 메인 클래스 - Nori Analyzer 적용"""
    
    def __init__(self):
        self.pdf_processor = PDFProcessor()
        self.es_client = ElasticsearchClient()
        self.text_processor = TextProcessor()
        self.index_name = "legal_documents_v2"  # 새로운 인덱스명
        
    def initialize_index(self, pdf_path: str, recreate: bool = False) -> bool:
        """PDF 파일을 인덱싱하여 검색 준비 - Nori 분석기 적용"""
        try:
            logger.info(f"인덱스 초기화 시작 (Nori 분석기 적용): {pdf_path}")
            
            # Nori 분석기가 적용된 인덱스 생성
            if not self._create_index_with_nori(recreate):
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
    
    def _create_index_with_nori(self, recreate: bool = False) -> bool:
        """Nori 분석기가 적용된 인덱스 생성"""
        try:
            if not self.es_client.client:
                logger.error("Elasticsearch 클라이언트가 연결되지 않았습니다.")
                return False
            
            # 기존 인덱스 삭제 (재생성 시)
            if recreate and self.es_client.client.indices.exists(index=self.index_name):
                self.es_client.client.indices.delete(index=self.index_name)
                logger.info("기존 인덱스 삭제 완료")
            
            # 인덱스가 이미 존재하면 스킵
            if self.es_client.client.indices.exists(index=self.index_name):
                logger.info("인덱스가 이미 존재합니다.")
                return True
            
            # Nori 분석기 설정
            index_config = {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "analysis": {
                        "tokenizer": {
                            "nori_custom": {
                                "type": "nori_tokenizer",
                                "decompound_mode": "mixed",  # 복합어 분해 모드
                                "user_dictionary_rules": [
                                    "개인정보보호",
                                    "정보주체",
                                    "스토킹처벌법",
                                    "성폭력처벌법",
                                    "사행산업통합감독위원회",
                                    "디지털성범죄",
                                    "온라인성착취",
                                    "데이터보호",
                                    "프라이버시",
                                    "사이버범죄"
                                ]
                            }
                        },
                        "filter": {
                            "nori_pos_filter": {
                                "type": "nori_part_of_speech",
                                "stoptags": [
                                    "E",    # 어미
                                    "IC",   # 감탄사
                                    "J",    # 조사
                                    "MAG",  # 일반 부사
                                    "MM",   # 관형사
                                    "SP",   # 구두점
                                    "SSC",  # 닫는 괄호
                                    "SSO",  # 여는 괄호
                                    "SC",   # 구분자
                                    "SE",   # 줄임표
                                    "XPN",  # 접두사
                                    "XSN",  # 명사파생 접미사
                                    "XSV",  # 동사파생 접미사
                                    "UNA",  # 알 수 없음
                                    "NA",   # 분석불능범주
                                    "VSV"   # 반복 동사
                                ]
                            },
                            "korean_synonym": {
                                "type": "synonym",
                                "synonyms": [
                                    "국가,정부,공공기관",
                                    "개인정보,사생활,프라이버시",
                                    "책무,의무,책임,임무",
                                    "보호,보장,안전",
                                    "스토킹,스토커,따라다니기",
                                    "성폭력,성범죄,성추행",
                                    "도박,사행행위,도박행위",
                                    "처벌,제재,벌칙,형벌"
                                ]
                            }
                        },
                        "analyzer": {
                            "korean_legal": {
                                "type": "custom",
                                "tokenizer": "nori_custom",
                                "filter": [
                                    "nori_pos_filter",
                                    "korean_synonym",
                                    "lowercase"
                                ]
                            }
                        }
                    }
                },
                "mappings": {
                    "properties": {
                        "title": {
                            "type": "text",
                            "analyzer": "korean_legal",
                            "search_analyzer": "korean_legal",
                            "fields": {
                                "keyword": {
                                    "type": "keyword"
                                }
                            }
                        },
                        "content": {
                            "type": "text",
                            "analyzer": "korean_legal",
                            "search_analyzer": "korean_legal"
                        },
                        "category": {
                            "type": "keyword"
                        },
                        "page_number": {
                            "type": "integer"
                        },
                        "file_path": {
                            "type": "keyword"
                        },
                        "law_name": {
                            "type": "keyword"
                        },
                        "article_number": {
                            "type": "keyword"
                        }
                    }
                }
            }
            
            # 인덱스 생성
            response = self.es_client.client.indices.create(
                index=self.index_name,
                body=index_config
            )
            
            logger.info(f"Nori 분석기가 적용된 인덱스 생성 완료: {self.index_name}")
            return True
            
        except Exception as e:
            logger.error(f"Nori 인덱스 생성 오류: {str(e)}")
            return False
    
    def analyze_search_terms(self, text: str) -> Dict:
        """텍스트가 어떻게 분석되는지 확인하는 도구"""
        try:
            if not self.es_client.client:
                logger.error("Elasticsearch 클라이언트가 연결되지 않았습니다.")
                return {
                    "original_text": text,
                    "analyzed_tokens": [],
                    "token_count": 0,
                    "error": "클라이언트 연결 없음"
                }
            
            analyze_query = {
                "analyzer": "korean_legal",
                "text": text
            }
            
            response = self.es_client.client.indices.analyze(
                index=self.index_name,
                body=analyze_query
            )
            
            tokens = [token['token'] for token in response['tokens']]
            
            return {
                "original_text": text,
                "analyzed_tokens": tokens,
                "token_count": len(tokens)
            }
            
        except Exception as e:
            logger.error(f"검색어 분석 오류: {str(e)}")
            return {
                "original_text": text,
                "analyzed_tokens": [],
                "token_count": 0,
                "error": str(e)
            }
    
    def search_with_advanced_analysis(self, query: str, size: int = 10, category: Optional[str] = None) -> List[SearchResult]:
        """향상된 텍스트 분석을 사용한 검색"""
        try:
            logger.info(f"향상된 검색 시작: '{query}'")
            
            # 기본 쿼리 구성
            search_query = {
                "query": {
                    "bool": {
                        "should": [
                            # 정확한 구문 매칭 (높은 점수)
                            {
                                "match_phrase": {
                                    "content": {
                                        "query": query,
                                        "boost": 3.0
                                    }
                                }
                            },
                            # 제목에서 매칭 (높은 점수)
                            {
                                "match": {
                                    "title": {
                                        "query": query,
                                        "boost": 2.5,
                                        "operator": "and"
                                    }
                                }
                            },
                            # 내용에서 매칭 (기본 점수)
                            {
                                "match": {
                                    "content": {
                                        "query": query,
                                        "boost": 1.0
                                    }
                                }
                            },
                            # 퍼지 검색 (오타 허용)
                            {
                                "fuzzy": {
                                    "content": {
                                        "value": query,
                                        "fuzziness": "AUTO",
                                        "boost": 0.5
                                    }
                                }
                            }
                        ],
                        "minimum_should_match": 1
                    }
                },
                "highlight": {
                    "fields": {
                        "title": {
                            "pre_tags": ["<mark>"],
                            "post_tags": ["</mark>"],
                            "fragment_size": 100,
                            "number_of_fragments": 1
                        },
                        "content": {
                            "pre_tags": ["<mark>"],
                            "post_tags": ["</mark>"],
                            "fragment_size": 150,
                            "number_of_fragments": 3
                        }
                    }
                },
                "size": size
            }
            
            # 카테고리 필터 추가
            if category:
                search_query["query"]["bool"]["filter"] = [
                    {"term": {"category": category}}
                ]
            
            # 검색 실행
            if not self.es_client.client:
                logger.error("Elasticsearch 클라이언트가 연결되지 않았습니다.")
                return []
            
            response = self.es_client.client.search(
                index=self.index_name,
                body=search_query
            )
            
            # 결과 처리
            results = []
            for hit in response['hits']['hits']:
                document = Document(
                    title=hit['_source'].get('title', ''),
                    content=hit['_source'].get('content', ''),
                    page_number=hit['_source'].get('page_number', 0),
                    category=hit['_source'].get('category', ''),
                    file_path=hit['_source'].get('file_path', '')
                )
                
                result = SearchResult(
                    document=document,
                    score=hit['_score'],
                    highlights=hit.get('highlight', {})
                )
                results.append(result)
            
            logger.info(f"향상된 검색 완료: {len(results)}개 결과")
            return results
            
        except Exception as e:
            logger.error(f"향상된 검색 오류: {str(e)}")
            return []
    
    def search(self, query: str, size: int = 10, category: Optional[str] = None) -> List[SearchResult]:
        """기본 검색 메서드 - 향상된 분석 사용"""
        return self.search_with_advanced_analysis(query, size, category)
    
    def search_by_category(self, category: str, size: int = 10) -> List[SearchResult]:
        """카테고리별 문서 검색"""
        try:
            logger.info(f"카테고리 검색: {category}")
            
            search_query = {
                "query": {
                    "term": {
                        "category": category
                    }
                },
                "size": size
            }
            
            if not self.es_client.client:
                logger.error("Elasticsearch 클라이언트가 연결되지 않았습니다.")
                return []
            
            response = self.es_client.client.search(
                index=self.index_name,
                body=search_query
            )
            
            results = []
            for hit in response['hits']['hits']:
                document = Document(
                    title=hit['_source'].get('title', ''),
                    content=hit['_source'].get('content', ''),
                    page_number=hit['_source'].get('page_number', 0),
                    category=hit['_source'].get('category', ''),
                    file_path=hit['_source'].get('file_path', '')
                )
                
                result = SearchResult(
                    document=document,
                    score=hit['_score'],
                    highlights={}
                )
                results.append(result)
            
            logger.info(f"카테고리 검색 완료: {len(results)}개 결과")
            return results
            
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
                index=self.index_name,
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
                "total_documents": self._get_document_count(),
                "elasticsearch_status": self.es_client.health_check(),
                "categories": self._get_category_stats(),
                "index_name": self.index_name,
                "analyzer_info": "korean_legal (Nori tokenizer)"
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"통계 조회 오류: {str(e)}")
            return {"error": str(e)}
    
    def _get_document_count(self) -> int:
        """문서 수 조회"""
        try:
            if not self.es_client.client:
                logger.error("Elasticsearch 클라이언트가 연결되지 않았습니다.")
                return 0
            
            response = self.es_client.client.count(index=self.index_name)
            return response['count']
        except Exception as e:
            logger.error(f"문서 수 조회 오류: {str(e)}")
            return 0
    
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
                index=self.index_name,
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
            if not self.es_client.client:
                logger.error("Elasticsearch 클라이언트가 연결되지 않았습니다.")
                return False
            
            if self.es_client.client.indices.exists(index=self.index_name):
                self.es_client.client.indices.delete(index=self.index_name)
                logger.info(f"인덱스 삭제 완료: {self.index_name}")
            return True
        except Exception as e:
            logger.error(f"인덱스 초기화 오류: {str(e)}")
            return False 