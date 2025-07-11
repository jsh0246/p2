"""
대한민국 법령 문서 검색 프로그램
Elasticsearch를 이용한 PDF 문서 검색 시스템
"""

import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

# 상대 경로 import를 위한 경로 설정
sys.path.append(str(Path(__file__).parent))

from services.search_service import SearchService
from models.document import SearchResult

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LegalDocumentSearchApp:
    """법령 문서 검색 애플리케이션"""
    
    def __init__(self):
        self.search_service = SearchService()
        self.pdf_path = "../pdf/laws.pdf"  # 법령 문서 경로
        self.is_initialized = False
        
    def initialize(self, recreate_index: bool = False) -> bool:
        """검색 시스템 초기화"""
        try:
            logger.info("=== 법령 문서 검색 시스템 초기화 ===")
            
            # PDF 파일 존재 확인
            if not Path(self.pdf_path).exists():
                logger.error(f"PDF 파일을 찾을 수 없습니다: {self.pdf_path}")
                return False
            
            # 인덱스 초기화 및 문서 인덱싱
            if self.search_service.initialize_index(self.pdf_path, recreate=recreate_index):
                self.is_initialized = True
                logger.info("초기화 완료!")
                
                # 통계 정보 출력
                stats = self.search_service.get_statistics()
                self._print_statistics(stats)
                
                return True
            else:
                logger.error("초기화 실패")
                return False
                
        except Exception as e:
            logger.error(f"초기화 중 오류 발생: {str(e)}")
            return False
    
    def search_documents(self, query: str, size: int = 5, category: Optional[str] = None) -> List[SearchResult]:
        """문서 검색"""
        if not self.is_initialized:
            logger.error("시스템이 초기화되지 않았습니다. initialize()를 먼저 실행하세요.")
            return []
        
        try:
            logger.info(f"검색어: '{query}'")
            
            # 검색 실행
            results = self.search_service.search(query, size=size, category=category)
            
            if results:
                self._print_search_results(results)
            else:
                print("검색 결과가 없습니다.")
            
            return results
            
        except Exception as e:
            logger.error(f"검색 중 오류 발생: {str(e)}")
            return []
    
    def search_by_category(self, category: str, size: int = 5) -> List[SearchResult]:
        """카테고리별 검색"""
        if not self.is_initialized:
            logger.error("시스템이 초기화되지 않았습니다.")
            return []
        
        try:
            logger.info(f"카테고리 검색: {category}")
            results = self.search_service.search_by_category(category, size=size)
            
            if results:
                self._print_search_results(results)
            else:
                print(f"'{category}' 카테고리에서 검색 결과가 없습니다.")
            
            return results
            
        except Exception as e:
            logger.error(f"카테고리 검색 중 오류 발생: {str(e)}")
            return []
    
    def _print_search_results(self, results: List[SearchResult]):
        """검색 결과 출력"""
        print("\n" + "="*80)
        print(f"검색 결과: {len(results)}개")
        print("="*80)
        
        for i, result in enumerate(results, 1):
            doc = result.document
            print(f"\n[{i}] 페이지 {doc.page_number} - 카테고리: {doc.category}")
            print(f"제목: {doc.title}")
            print(f"점수: {result.score:.2f}")
            
            # 하이라이트된 내용 출력
            if result.highlights and 'content' in result.highlights:
                print(f"내용: {result.highlights['content'][0]}")
            else:
                # 내용의 일부만 출력
                content_preview = doc.content[:200] + "..." if len(doc.content) > 200 else doc.content
                print(f"내용: {content_preview}")
            
            # Explanation 정보 출력
            if result.explanation:
                self._print_explanation(result.explanation)
            
            print("-" * 80)
    
    def _print_statistics(self, stats: dict):
        """통계 정보 출력"""
        print("\n" + "="*50)
        print("시스템 통계")
        print("="*50)
        print(f"총 문서 수: {stats.get('total_documents', 0)}")
        
        if 'categories' in stats:
            print("\n카테고리별 문서 수:")
            for category, count in stats['categories'].items():
                print(f"  - {category}: {count}개")
        
        es_status = stats.get('elasticsearch_status', {})
        print(f"\nElasticsearch 상태: {es_status.get('status', 'unknown')}")
        print("="*50)
    
    def _print_explanation(self, explanation: dict):
        """검색 점수 계산 설명 출력"""
        print("📊 점수 계산 설명:")
        
        if not explanation:
            print("  설명 정보가 없습니다.")
            return
        
        try:
            # 재귀적으로 explanation 구조를 파싱
            self._print_explanation_recursive(explanation, indent=1)
        except Exception as e:
            print(f"  설명 정보 처리 중 오류: {str(e)}")
        
        print()
    
    def _print_explanation_recursive(self, explanation: dict, indent: int = 0):
        """재귀적으로 explanation 구조를 파싱하여 출력"""
        if not isinstance(explanation, dict):
            return
        
        # 깊이 제한 (너무 깊게 들어가지 않도록)
        if indent > 4:
            return
        
        indent_str = "  " * indent
        
        # 점수와 설명 출력
        value = explanation.get('value', 'N/A')
        description = explanation.get('description', '')
        
        # 설명을 더 이해하기 쉽게 번역
        korean_desc = self._translate_explanation_description(description)
        
        # 최상위 레벨에서만 점수 출력
        if indent == 1:
            print(f"{indent_str}- {korean_desc}: {value:.4f}")
        else:
            # 하위 레벨에서는 더 간단히 표시
            if korean_desc and korean_desc != "점수 계산":
                print(f"{indent_str}• {korean_desc}: {value:.4f}")
        
        # 세부 설명이 있는 경우 재귀적으로 처리
        if 'details' in explanation and explanation['details']:
            details = explanation['details']
            if isinstance(details, list):
                # 점수가 높은 순으로 정렬하여 상위 4개만 출력
                sorted_details = sorted(details, 
                                      key=lambda x: x.get('value', 0) if isinstance(x, dict) else 0, 
                                      reverse=True)[:4]
                
                # 만약 "sum of" 타입이면 더 자세히 설명
                if "sum of" in description.lower():
                    for detail in sorted_details:
                        if isinstance(detail, dict):
                            self._print_explanation_recursive(detail, indent + 1)
                # "max of" 타입이면 각 그룹을 구분해서 표시
                elif "max of" in description.lower():
                    for i, detail in enumerate(sorted_details):
                        if isinstance(detail, dict):
                            detail_desc = detail.get('description', '')
                            if 'sum of' in detail_desc.lower():
                                # 필드별로 구분해서 표시 - 더 정확한 필드 구분
                                field_name = self._determine_field_name(detail)
                                print(f"{indent_str}  [{field_name}]")
                                self._print_explanation_recursive(detail, indent + 2)
                            else:
                                self._print_explanation_recursive(detail, indent + 1)
                else:
                    # 기타 경우
                    for detail in sorted_details:
                        if isinstance(detail, dict):
                            self._print_explanation_recursive(detail, indent + 1)
            elif isinstance(details, dict):
                self._print_explanation_recursive(details, indent + 1)
    
    def _translate_explanation_description(self, description: str) -> str:
        """Elasticsearch explanation 설명을 한국어로 번역"""
        if not description:
            return ""
        
        # 콜론 중복 제거
        cleaned_desc = description.rstrip(':')
        
        # 복잡한 패턴 매칭과 번역
        import re
        
        # weight(...) 패턴 처리
        weight_pattern = r'weight\(([^)]+)\)'
        weight_match = re.search(weight_pattern, cleaned_desc)
        if weight_match:
            field_info = weight_match.group(1)
            if 'title:' in field_info:
                return f"제목 필드 가중치 ('{field_info.split('title:')[1].split()[0]}')"
            elif 'content:' in field_info:
                search_term = field_info.split('content:')[1].split()[0]
                return f"내용 필드 가중치 ('{search_term}')"
        
        # score(...) 패턴 처리
        if 'score(' in cleaned_desc and 'freq=' in cleaned_desc:
            freq_match = re.search(r'freq=(\d+\.?\d*)', cleaned_desc)
            if freq_match:
                freq = freq_match.group(1)
                return f"점수 계산 (빈도: {freq})"
        
        # 간단한 용어 번역
        simple_translations = {
            "sum of": "필드 점수 합계",
            "max of": "최고 점수 선택", 
            "min of": "최소값",
            "product of": "곱셈",
            "fieldWeight": "필드 가중치",
            "tf": "단어 빈도",
            "idf": "역문서 빈도",
            "norm": "정규화",
            "boost": "부스트",
            "match": "매칭"
        }
        
        result = cleaned_desc
        for en, ko in simple_translations.items():
            if en in result:
                result = ko
                break
        
        # 너무 기술적인 설명은 간단히 변환
        if any(tech in cleaned_desc.lower() for tech in ['perfieldsimilarity', 'result of', 'computed as']):
            if 'title' in cleaned_desc:
                return "제목 매칭 점수"
            elif 'content' in cleaned_desc:
                return "내용 매칭 점수"
            else:
                return "매칭 점수"
        
        return result if result != cleaned_desc else "점수 계산"
    
    def _determine_field_name(self, detail: dict) -> str:
        """detail 정보를 분석해서 어떤 필드인지 결정"""
        if not isinstance(detail, dict):
            return "알 수 없는 필드"
        
        # details 안에 있는 모든 weight 정보를 확인
        details = detail.get('details', [])
        if not details:
            return "알 수 없는 필드"
        
        # 첫 번째 detail의 설명을 확인
        first_detail = details[0] if details else {}
        first_desc = first_detail.get('description', '') if isinstance(first_detail, dict) else ''
        
        # weight 패턴에서 필드명 추출
        if 'title:' in first_desc.lower():
            return "제목 필드"
        elif 'content:' in first_desc.lower():
            return "내용 필드"
        else:
            return "알 수 없는 필드"
    
    def interactive_search(self):
        """대화형 검색 모드"""
        print("\n🔍 대한민국 법령 문서 검색 시스템")
        print("=" * 60)
        print("사용 가능한 명령어:")
        print("  - 검색어 입력: 단어나 구문을 입력하여 검색")
        print("  - category:<카테고리명>: 특정 카테고리에서 검색")
        print("  - stats: 시스템 통계 보기")
        print("  - help: 도움말 보기")
        print("  - quit: 종료")
        print("=" * 60)
        
        while True:
            try:
                user_input = input("\n검색어를 입력하세요 (quit으로 종료): ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("검색을 종료합니다.")
                    break
                
                elif user_input.lower() in ['help', 'h']:
                    self._print_help()
                
                elif user_input.lower() in ['stats', 'stat']:
                    stats = self.search_service.get_statistics()
                    self._print_statistics(stats)
                
                elif user_input.startswith('category:'):
                    category = user_input[9:].strip()
                    if category:
                        self.search_by_category(category)
                    else:
                        print("카테고리를 입력해주세요. 예: category:스토킹")
                
                else:
                    # 일반 검색
                    self.search_documents(user_input)
                
            except KeyboardInterrupt:
                print("\n\n검색을 종료합니다.")
                break
            except EOFError:
                print("\n\n검색을 종료합니다.")
                break
            except Exception as e:
                logger.error(f"명령어 처리 중 오류 발생: {str(e)}")
                print("오류가 발생했습니다. 다시 시도해주세요.")
    
    def _print_help(self):
        """도움말 출력"""
        print("\n📖 사용법:")
        print("1. 키워드 검색: '스토킹', '성폭력', '도박' 등")
        print("2. 구문 검색: '스토킹 처벌법', '성폭력 예방' 등")
        print("3. 카테고리 검색: 'category:스토킹', 'category:성폭력', 'category:사행산업'")
        print("4. 시스템 상태: 'stats'")
        print("5. 종료: 'quit'")
        print("\n💡 팁: 여러 단어를 입력하면 더 정확한 검색 결과를 얻을 수 있습니다.")

def main():
    """메인 함수"""
    try:
        # 애플리케이션 초기화
        app = LegalDocumentSearchApp()
        
        print("🏛️  대한민국 법령 문서 검색 시스템")
        print("=" * 60)
        print("초기화 중...")
        
        # 시스템 초기화
        if not app.initialize():
            print("❌ 시스템 초기화에 실패했습니다.")
            print("Elasticsearch가 실행 중인지 확인해주세요.")
            return
        
        print("✅ 시스템 초기화 완료!")
        
        # 명령행 인자 처리
        if len(sys.argv) > 1:
            # 명령행에서 검색어가 주어진 경우
            query = " ".join(sys.argv[1:])
            print(f"\n검색어: {query}")
            app.search_documents(query)
        else:
            # 대화형 모드
            app.interactive_search()
        
    except KeyboardInterrupt:
        print("\n\n프로그램을 종료합니다.")
    except Exception as e:
        logger.error(f"프로그램 실행 중 오류 발생: {str(e)}")
        print("오류가 발생했습니다. 로그를 확인해주세요.")

if __name__ == "__main__":
    main()
