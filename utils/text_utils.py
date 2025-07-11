"""
텍스트 처리 유틸리티
"""

import re
from typing import List, Dict, Any

class TextProcessor:
    """텍스트 처리를 위한 유틸리티 클래스"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """텍스트를 정리하고 불필요한 공백 제거"""
        if not text:
            return ""
        
        # 연속된 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        # 앞뒤 공백 제거
        text = text.strip()
        
        # 특수 문자 정리 (기본적인 정리만)
        text = re.sub(r'[^\w\s가-힣]', ' ', text)
        
        return text
    
    @staticmethod
    def extract_keywords(text: str, min_length: int = 2) -> List[str]:
        """텍스트에서 키워드 추출"""
        if not text:
            return []
        
        # 텍스트 정리
        clean_text = TextProcessor.clean_text(text)
        
        # 단어 분리
        words = clean_text.split()
        
        # 최소 길이 이상의 단어만 선택
        keywords = [word for word in words if len(word) >= min_length]
        
        return keywords
    
    @staticmethod
    def highlight_text(text: str, keywords: List[str], max_length: int = 200) -> str:
        """텍스트에서 키워드 하이라이트 및 요약"""
        if not text or not keywords:
            return text[:max_length] + "..." if len(text) > max_length else text
        
        # 키워드가 포함된 부분 찾기
        for keyword in keywords:
            if keyword in text:
                # 키워드 위치 찾기
                pos = text.find(keyword)
                
                # 키워드 주변 텍스트 추출
                start = max(0, pos - max_length // 2)
                end = min(len(text), pos + max_length // 2)
                
                highlighted_text = text[start:end]
                
                # 키워드 하이라이트
                highlighted_text = highlighted_text.replace(keyword, f"**{keyword}**")
                
                if start > 0:
                    highlighted_text = "..." + highlighted_text
                if end < len(text):
                    highlighted_text = highlighted_text + "..."
                
                return highlighted_text
        
        return text[:max_length] + "..." if len(text) > max_length else text
    
    @staticmethod
    def split_into_chunks(text: str, max_chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """긴 텍스트를 청크로 분할"""
        if not text:
            return []
        
        if len(text) <= max_chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + max_chunk_size, len(text))
            
            # 단어 경계에서 자르기
            if end < len(text):
                last_space = text.rfind(' ', start, end)
                if last_space > start:
                    end = last_space
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            if start <= 0:
                break
        
        return chunks
    
    @staticmethod
    def categorize_content(text: str) -> str:
        """텍스트 내용을 기반으로 카테고리 분류"""
        text_lower = text.lower()
        
        # 키워드 기반 분류
        stalking_keywords = ['스토킹', '괴롭힘', '추적', '감시', '접근금지']
        violence_keywords = ['성폭력', '성추행', '성희롱', '강간', '추행']
        gambling_keywords = ['도박', '사행', '카지노', '경마', '복권', '게임']
        
        stalking_count = sum(1 for keyword in stalking_keywords if keyword in text_lower)
        violence_count = sum(1 for keyword in violence_keywords if keyword in text_lower)
        gambling_count = sum(1 for keyword in gambling_keywords if keyword in text_lower)
        
        # 가장 많이 매칭된 카테고리 반환
        if stalking_count >= violence_count and stalking_count >= gambling_count:
            return "스토킹"
        elif violence_count >= stalking_count and violence_count >= gambling_count:
            return "성폭력"
        elif gambling_count >= stalking_count and gambling_count >= violence_count:
            return "사행산업"
        else:
            return "기타" 