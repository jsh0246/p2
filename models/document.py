"""
문서 모델 클래스
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class Document:
    """PDF 문서 페이지를 나타내는 모델"""
    
    title: str
    content: str
    page_number: int
    category: str
    file_path: str
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Elasticsearch 인덱싱을 위한 딕셔너리 변환"""
        return {
            'title': self.title,
            'content': self.content,
            'page_number': self.page_number,
            'category': self.category,
            'file_path': self.file_path,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Document':
        """딕셔너리에서 Document 객체 생성"""
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'])
        
        return cls(
            title=data['title'],
            content=data['content'],
            page_number=data['page_number'],
            category=data['category'],
            file_path=data['file_path'],
            created_at=created_at
        )

@dataclass
class SearchResult:
    """검색 결과를 나타내는 모델"""
    
    document: Document
    score: float
    highlights: Optional[Dict[str, list]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """검색 결과를 딕셔너리로 변환"""
        return {
            'document': self.document.to_dict(),
            'score': self.score,
            'highlights': self.highlights
        } 