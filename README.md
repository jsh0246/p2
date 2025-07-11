# 대한민국 법령 문서 검색 시스템

Elasticsearch를 이용한 PDF 문서 검색 프로그램입니다.

## 기능

- **키워드 검색**: 하나 또는 여러 단어로 PDF 문서 검색
- **카테고리 검색**: 스토킹, 성폭력, 사행산업 카테고리별 검색
- **하이라이트**: 검색어가 포함된 부분 강조 표시
- **통계 정보**: 문서 수, 카테고리별 분포 등

## 프로젝트 구조

```
p2/
├── main.py                     # 메인 실행 파일
├── config/
│   └── settings.py            # Elasticsearch 설정
├── services/
│   ├── pdf_processor.py       # PDF 처리 서비스
│   ├── elasticsearch_client.py # Elasticsearch 클라이언트
│   └── search_service.py      # 검색 서비스
├── models/
│   └── document.py            # 문서 모델
└── utils/
    └── text_utils.py          # 텍스트 처리 유틸리티
```

## 사용 방법

### 1. 기본 실행
```bash
cd p2
uv run python main.py
```

### 2. 명령행에서 직접 검색
```bash
cd p2
uv run python main.py "스토킹"
uv run python main.py "성폭력 예방"
```

### 3. 대화형 모드 명령어
- `검색어 입력`: 일반 검색
- `category:스토킹`: 특정 카테고리에서 검색
- `stats`: 시스템 통계 보기
- `help`: 도움말 보기
- `quit`: 종료

## 환경 설정

### 환경 변수
- `ELASTICSEARCH_HOST`: Elasticsearch 호스트 (기본값: localhost)
- `ELASTICSEARCH_PORT`: Elasticsearch 포트 (기본값: 9200)
- `ELASTICSEARCH_USERNAME`: 사용자명 (기본값: elastic)
- `ELASTICSEARCH_PASSWORD`: 비밀번호 (기본값: changeme)
- `ELASTICSEARCH_INDEX`: 인덱스 이름 (기본값: legal_documents)

### 필요한 파일
- `../pdf/laws.pdf`: 법령 문서 PDF 파일 (약 180페이지)

## 주요 클래스

### LegalDocumentSearchApp
- 메인 애플리케이션 클래스
- 사용자 인터페이스 제공
- 검색 기능 통합

### SearchService
- 검색 서비스 총괄
- PDF 처리와 Elasticsearch 연동
- 검색 결과 후처리

### ElasticsearchClient
- Elasticsearch 연결 관리
- 인덱스 생성/삭제
- 문서 인덱싱/검색

### PDFProcessor
- PDF 파일 텍스트 추출
- 페이지별 문서 분리
- 자동 카테고리 분류

## 검색 예시

```python
# 키워드 검색
app.search_documents("스토킹")

# 카테고리별 검색
app.search_by_category("성폭력")

# 복수 키워드 검색
app.search_documents("스토킹 처벌법")
```

## 오류 해결

### Elasticsearch 연결 오류
- Elasticsearch 서버가 실행 중인지 확인
- 포트 번호와 인증 정보 확인

### PDF 파일 오류
- `../pdf/laws.pdf` 파일 존재 확인
- 파일 접근 권한 확인

### 메모리 부족
- 대용량 PDF 처리 시 메모리 사용량 증가
- 청크 단위 처리 고려 