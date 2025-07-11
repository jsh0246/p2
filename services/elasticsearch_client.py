"""
Elasticsearch 클라이언트 서비스
"""

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, NotFoundError
import logging
from typing import List, Dict, Any, Optional

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import config
from models.document import Document, SearchResult

logger = logging.getLogger(__name__)

class ElasticsearchClient:
    """Elasticsearch 클라이언트를 관리하는 클래스"""
    
    def __init__(self):
        self.client = None
        self.index_name = config.index_name
        self._connect()
    
    def _connect(self):
        """Elasticsearch에 연결"""
        try:
            connection_config = config.get_connection_config()
            self.client = Elasticsearch(**connection_config)
            
            # 연결 테스트
            if self.client.ping():
                logger.info("Elasticsearch 연결 성공")
            else:
                logger.error("Elasticsearch 연결 실패")
                
        except ConnectionError as e:
            logger.error(f"Elasticsearch 연결 오류: {str(e)}")
            self.client = None
        except Exception as e:
            logger.error(f"Elasticsearch 초기화 오류: {str(e)}")
            self.client = None
    
    def create_index(self, delete_existing: bool = False) -> bool:
        """인덱스 생성"""
        if not self.client:
            logger.error("Elasticsearch 클라이언트가 연결되지 않았습니다.")
            return False
        
        try:
            # 기존 인덱스 삭제
            if delete_existing and self.client.indices.exists(index=self.index_name):
                self.client.indices.delete(index=self.index_name)
                logger.info(f"기존 인덱스 삭제됨: {self.index_name}")
            
            # 인덱스가 존재하지 않는 경우에만 생성
            if not self.client.indices.exists(index=self.index_name):
                index_settings = config.get_index_settings()
                self.client.indices.create(
                    index=self.index_name,
                    body=index_settings
                )
                logger.info(f"인덱스 생성됨: {self.index_name}")
            else:
                logger.info(f"인덱스가 이미 존재함: {self.index_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"인덱스 생성 오류: {str(e)}")
            return False
    
    def index_document(self, document: Document) -> bool:
        """단일 문서 인덱싱"""
        if not self.client:
            logger.error("Elasticsearch 클라이언트가 연결되지 않았습니다.")
            return False
        
        try:
            doc_dict = document.to_dict()
            response = self.client.index(
                index=self.index_name,
                body=doc_dict
            )
            
            logger.debug(f"문서 인덱싱 성공: 페이지 {document.page_number}")
            return True
            
        except Exception as e:
            logger.error(f"문서 인덱싱 오류: {str(e)}")
            return False
    
    def bulk_index_documents(self, documents: List[Document]) -> bool:
        """벌크 문서 인덱싱"""
        if not self.client:
            logger.error("Elasticsearch 클라이언트가 연결되지 않았습니다.")
            return False
        
        if not documents:
            logger.warning("인덱싱할 문서가 없습니다.")
            return True
        
        try:
            # 벌크 요청 데이터 준비
            bulk_data = []
            for doc in documents:
                # 액션 메타데이터
                bulk_data.append({
                    "index": {
                        "_index": self.index_name
                    }
                })
                # 실제 문서 데이터
                bulk_data.append(doc.to_dict())
            
            # 벌크 인덱싱 실행
            response = self.client.bulk(
                body=bulk_data,
                refresh=True
            )
            
            # 오류 확인
            if response.get('errors'):
                logger.error("벌크 인덱싱 중 일부 오류 발생")
                for item in response['items']:
                    if 'index' in item and 'error' in item['index']:
                        logger.error(f"인덱싱 오류: {item['index']['error']}")
                return False
            
            logger.info(f"벌크 인덱싱 성공: {len(documents)}개 문서")
            return True
            
        except Exception as e:
            logger.error(f"벌크 인덱싱 오류: {str(e)}")
            return False
    
    def search(self, query: str, size: int = 10, category: Optional[str] = None) -> List[SearchResult]:
        """문서 검색"""
        if not self.client:
            logger.error("Elasticsearch 클라이언트가 연결되지 않았습니다.")
            return []
        
        try:
            # 검색 쿼리 구성
            search_body = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "multi_match": {
                                    "query": query,
                                    "fields": ["title^2", "content"],
                                    "type": "best_fields",
                                    "fuzziness": "AUTO"
                                }
                            }
                        ]
                    }
                },
                "highlight": {
                    "fields": {
                        "title": {},
                        "content": {
                            "fragment_size": 200,
                            "number_of_fragments": 3
                        }
                    }
                },
                "size": size,
                "sort": [
                    {"_score": {"order": "desc"}}
                ],
                "explain": True
            }
            
            # 카테고리 필터 추가
            if category:
                search_body["query"]["bool"]["filter"] = [
                    {"term": {"category": category}}
                ]
            
            # 검색 실행
            response = self.client.search(
                index=self.index_name,
                body=search_body
            )
            
            # 검색 결과 처리
            search_results = []
            for hit in response['hits']['hits']:
                document = Document.from_dict(hit['_source'])
                
                search_result = SearchResult(
                    document=document,
                    score=hit['_score'],
                    highlights=hit.get('highlight', {}),
                    explanation=hit.get('_explanation', {})
                )
                
                search_results.append(search_result)
            
            logger.info(f"검색 완료: '{query}' - {len(search_results)}개 결과")
            return search_results
            
        except Exception as e:
            logger.error(f"검색 오류: {str(e)}")
            return []
    
    def get_document_count(self) -> int:
        """인덱스의 문서 수 반환"""
        if not self.client:
            return 0
        
        try:
            response = self.client.count(index=self.index_name)
            return response['count']
        except Exception as e:
            logger.error(f"문서 수 조회 오류: {str(e)}")
            return 0
    
    def delete_index(self) -> bool:
        """인덱스 삭제"""
        if not self.client:
            logger.error("Elasticsearch 클라이언트가 연결되지 않았습니다.")
            return False
        
        try:
            if self.client.indices.exists(index=self.index_name):
                self.client.indices.delete(index=self.index_name)
                logger.info(f"인덱스 삭제됨: {self.index_name}")
                return True
            else:
                logger.warning(f"삭제할 인덱스가 존재하지 않음: {self.index_name}")
                return True
                
        except Exception as e:
            logger.error(f"인덱스 삭제 오류: {str(e)}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Elasticsearch 상태 확인"""
        if not self.client:
            return {"status": "disconnected", "error": "클라이언트 연결 안됨"}
        
        try:
            # 클러스터 상태 확인
            health = self.client.cluster.health()
            
            # 인덱스 존재 확인
            index_exists = self.client.indices.exists(index=self.index_name)
            
            # 문서 수 확인
            doc_count = self.get_document_count() if index_exists else 0
            
            return {
                "status": "connected",
                "cluster_health": health['status'],
                "index_exists": index_exists,
                "document_count": doc_count,
                "index_name": self.index_name
            }
            
        except Exception as e:
            return {"status": "error", "error": str(e)} 