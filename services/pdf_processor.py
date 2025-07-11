"""
PDF 처리 서비스
"""

import pdfplumber
import logging
import sys
from typing import List, Dict, Any, Optional
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from models.document import Document
from utils.text_utils import TextProcessor

logger = logging.getLogger(__name__)

class PDFProcessor:
    """PDF 파일을 처리하는 서비스 클래스"""
    
    def __init__(self):
        self.text_processor = TextProcessor()
    
    def extract_text_from_pdf(self, pdf_path: str) -> List[Document]:
        """PDF 파일에서 텍스트를 추출하고 Document 객체 리스트로 반환"""
        documents = []
        
        try:
            pdf_path_obj = Path(pdf_path)
            
            if not pdf_path_obj.exists():
                logger.error(f"PDF 파일을 찾을 수 없습니다: {pdf_path_obj}")
                return documents
            
            with pdfplumber.open(pdf_path_obj) as pdf:
                logger.info(f"PDF 파일 처리 시작: {pdf_path_obj.name}, 총 페이지 수: {len(pdf.pages)}")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        # 페이지에서 텍스트 추출
                        text = page.extract_text()
                        
                        if text and text.strip():
                            # 텍스트 정리
                            cleaned_text = self.text_processor.clean_text(text)
                            
                            if cleaned_text:
                                # 카테고리 자동 분류
                                category = self.text_processor.categorize_content(cleaned_text)
                                
                                # 제목 생성 (첫 번째 줄 또는 첫 50자)
                                title = self._generate_title(cleaned_text, page_num)
                                
                                # Document 객체 생성
                                document = Document(
                                    title=title,
                                    content=cleaned_text,
                                    page_number=page_num,
                                    category=category,
                                    file_path=str(pdf_path_obj)
                                )
                                
                                documents.append(document)
                                logger.debug(f"페이지 {page_num} 처리 완료: {len(cleaned_text)} 문자")
                        else:
                            logger.warning(f"페이지 {page_num}에서 텍스트를 추출할 수 없습니다.")
                            
                    except Exception as e:
                        logger.error(f"페이지 {page_num} 처리 중 오류 발생: {str(e)}")
                        continue
                
                logger.info(f"PDF 처리 완료: {len(documents)}개 페이지 처리됨")
                
        except Exception as e:
            logger.error(f"PDF 파일 처리 중 오류 발생: {str(e)}")
        
        return documents
    
    def _generate_title(self, text: str, page_num: int) -> str:
        """페이지 제목 생성"""
        if not text:
            return f"페이지 {page_num}"
        
        # 첫 번째 줄을 제목으로 사용
        first_line = text.split('\n')[0].strip()
        
        if first_line and len(first_line) > 5:
            # 첫 번째 줄이 의미있는 제목인 경우
            return first_line[:100] + "..." if len(first_line) > 100 else first_line
        else:
            # 첫 50자를 제목으로 사용
            title = text[:50].strip()
            return title + "..." if len(text) > 50 else title
    
    def process_pdf_for_indexing(self, pdf_path: str) -> List[Dict[str, Any]]:
        """PDF를 인덱싱용으로 처리"""
        documents = self.extract_text_from_pdf(pdf_path)
        
        # Document 객체를 딕셔너리로 변환
        return [doc.to_dict() for doc in documents]
    
    def extract_pages_by_category(self, pdf_path: str, category: str) -> List[Document]:
        """특정 카테고리의 페이지만 추출"""
        all_documents = self.extract_text_from_pdf(pdf_path)
        
        return [doc for doc in all_documents if doc.category == category]
    
    def get_pdf_info(self, pdf_path: str) -> Dict[str, Any]:
        """PDF 파일 정보 반환"""
        try:
            pdf_path_obj = Path(pdf_path)
            
            if not pdf_path_obj.exists():
                return {"error": f"PDF 파일을 찾을 수 없습니다: {pdf_path_obj}"}
            
            with pdfplumber.open(pdf_path_obj) as pdf:
                info = {
                    "file_name": pdf_path_obj.name,
                    "file_path": str(pdf_path_obj),
                    "file_size": pdf_path_obj.stat().st_size,
                    "total_pages": len(pdf.pages),
                    "metadata": pdf.metadata if hasattr(pdf, 'metadata') else {}
                }
                
                return info
                
        except Exception as e:
            return {"error": f"PDF 정보를 가져올 수 없습니다: {str(e)}"}
    
    def search_text_in_pdf(self, pdf_path: str, query: str) -> List[Dict[str, Any]]:
        """PDF에서 특정 텍스트 검색"""
        documents = self.extract_text_from_pdf(pdf_path)
        results = []
        
        query_lower = query.lower()
        
        for doc in documents:
            if query_lower in doc.content.lower():
                # 하이라이트된 텍스트 생성
                highlighted_text = self.text_processor.highlight_text(
                    doc.content, 
                    [query], 
                    max_length=300
                )
                
                results.append({
                    "document": doc.to_dict(),
                    "highlighted_text": highlighted_text,
                    "relevance_score": doc.content.lower().count(query_lower)
                })
        
        # 관련성 점수로 정렬
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return results 