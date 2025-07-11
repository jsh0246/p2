"""
Elasticsearch 설정 파일
"""

import os
from typing import Dict, Any

class ElasticsearchConfig:
    """Elasticsearch 설정을 관리하는 클래스"""
    
    def __init__(self):
        self.host = os.getenv('ELASTICSEARCH_HOST', 'localhost')
        self.port = int(os.getenv('ELASTICSEARCH_PORT', '9200'))
        self.username = os.getenv('ELASTICSEARCH_USERNAME', 'elastic')
        self.password = os.getenv('ELASTICSEARCH_PASSWORD', 'slzR9p6H')
        self.index_name = os.getenv('ELASTICSEARCH_INDEX', 'legal_documents')
        self.use_ssl = os.getenv('ELASTICSEARCH_USE_SSL', 'false').lower() == 'true'
        self.verify_certs = os.getenv('ELASTICSEARCH_VERIFY_CERTS', 'false').lower() == 'true'
        
    def get_connection_config(self) -> Dict[str, Any]:
        """Elasticsearch 연결 설정을 반환합니다."""
        scheme = 'https' if self.use_ssl else 'http'
        return {
            'hosts': [f'{scheme}://{self.host}:{self.port}'],
            'basic_auth': (self.username, self.password),
            'verify_certs': self.verify_certs,
            'ssl_show_warn': False
        }
        
    def get_index_settings(self) -> Dict[str, Any]:
        """인덱스 설정을 반환합니다."""
        # return {
        #     "settings": {
        #         "analysis": {
        #             "analyzer": {
        #                 "korean_analyzer": {
        #                     "tokenizer": "nori_tokenizer_custom",
        #                     "filter": ["lowercase", "nori_part_of_speech"]
        #                 }
        #             }
        #         }
        #     },
        #     "mappings": {
        #         "properties": {
        #             "title": {"type": "text", "analyzer": "korean_analyzer"},
        #             "content": {"type": "text", "analyzer": "korean_analyzer"}
        #         }
        #     }
        # }
        # return {
        #     "settings": {
        #         "analysis": {
        #             "tokenizer": {
        #                 "nori_tokenizer_custom": {
        #                     "type": "nori_tokenizer",
        #                     "decompound_mode": "mixed",
        #                     "user_dictionary": "analysis-nori-user-dictionary.txt"
        #                 }
        #             },
        #             "filter": {
        #                 "nori_readingform": {
        #                     "type": "nori_reading_form"
        #                 },
        #                 "nori_part_of_speech": {
        #                     "type": "nori_part_of_speech",
        #                     "stoptags": [
        #                         "E",    # 어미
        #                         "J",    # 조사
        #                         "MAG",  # 일반 부사
        #                         "XR"    # 어근 외 확장 어근
        #                     ]
        #                 }
        #             },
        #             "analyzer": {
        #                 "korean_nori_analyzer": {
        #                     "type": "custom",
        #                     "tokenizer": "nori_tokenizer_custom",
        #                     "filter": [
        #                         "lowercase",
        #                         "nori_readingform",
        #                         "nori_part_of_speech"
        #                     ]
        #                 }
        #             }
        #         }
        #     },
        #     "mappings": {
        #         "properties": {
        #             "title": {
        #                 "type": "text",
        #                 "analyzer": "korean_nori_analyzer"
        #             },
        #             "content": {
        #                 "type": "text",
        #                 "analyzer": "korean_nori_analyzer"
        #             },
        #             "tags": {
        #                 "type": "keyword"
        #             },
        #             "published_date": {
        #                 "type": "date",
        #                 "format": "yyyy-MM-dd"
        #             }
        #         }
        #     }
        # }
        # return {
        #     "settings": {
        #         "analysis": {
        #             "tokenizer": {
        #                 "nori_tokenizer_custom": {
        #                     "type": "nori_tokenizer",
        #                     # 복합어 분해 방식: 'none'|'discard'|'mixed'
        #                     "decompound_mode": "mixed",
        #                     # 사용자 사전 파일 경로 (플러그인 설정에 따라 classpath 하위)
        #                     # "user_dictionary": "analysis-nori-user-dictionary.txt"
        #                 }
        #             },
        #             "filter": {
        #                 # 품사 필터를 추가하면 불필요한 품사(조사·어미 등)를 제거할 수 있음
        #                 "nori_part_of_speech": {
        #                     "type": "nori_part_of_speech",
        #                     "stoptags": [
        #                         "E",  # 어미
        #                         "J",  # 조사
        #                         "K",  # 부사격조사
        #                         "X"   # 기타구
        #                     ]
        #                 }
        #             },
        #             "analyzer": {
        #                 "my_korean_analyzer": {
        #                     "type": "custom",
        #                     "tokenizer": "nori_tokenizer_custom",
        #                     "filter": [
        #                         "lowercase",
        #                         "nori_part_of_speech"
        #                     ]
        #                 }
        #             }
        #         }
        #     },
        #     "mappings": {
        #         "properties": {
        #             "content": {
        #                 "type": "text",
        #                 "analyzer": "my_korean_analyzer"
        #             }
        #         }
        #     }
        # }

        # return {
        #     "settings": {
        #         "analysis": {
        #             # "analyzer": {
        #             #     "nori",
        #             # }
                        
        #             "analyzer": {
        #                 "youtube_analyzer": {
        #                     "tokenizer": "standard",
        #                     "filter": ["lowercase", "stop"]
        #                 }
        #             }
        #         },
        #         "number_of_shards": 1,
        #         "number_of_replicas": 0
        #     },
        #     "mappings": {
        #         "properties": {
        #             "title": {
        #                 "type": "text",
        #                 # "analyzer": "korean_analyzer"
        #                 "analyzer": "nori"
        #                 # "analyzer": "youtube_analyzer"
        #             },
        #             "content": {
        #                 "type": "text",
        #                 # "analyzer": "korean_analyzer"
        #                 "analyzer": "nori"
        #                 # "analyzer": "youtube_analyzer"
        #             },
        #             "page_number": {
        #                 "type": "integer"
        #             },
        #             "category": {
        #                 "type": "keyword"
        #             },
        #             "file_path": {
        #                 "type": "keyword"
        #             },
        #             "created_at": {
        #                 "type": "date"
        #             }
        #         }
        #     }
        # }

        return {
            "settings": {
                "analysis": {
                    "analyzer": {
                        "korean_analyzer": {
                            "tokenizer": "standard",
                            "filter": ["lowercase", "stop"]
                        }
                    }
                },
                "number_of_shards": 1,
                "number_of_replicas": 0
            },
            "mappings": {
                "properties": {
                    "title": {
                        "type": "text",
                        "analyzer": "korean_analyzer"
                        # "analyzer": "nori"
                    },
                    "content": {
                        "type": "text",
                        "analyzer": "korean_analyzer"
                        # "analyzer": "nori"
                    },
                    "page_number": {
                        "type": "integer"
                    },
                    "category": {
                        "type": "keyword"
                    },
                    "file_path": {
                        "type": "keyword"
                    },
                    "created_at": {
                        "type": "date"
                    }
                }
            }
        }

# 싱글톤 설정 인스턴스
config = ElasticsearchConfig() 