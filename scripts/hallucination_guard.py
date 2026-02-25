#!/usr/bin/env python3
"""
XIVIX Hallucination Guardrail v1.0
보험/금융 블로그 콘텐츠 발행 전 자동 검증 스크립트

사용법:
  python hallucination_guard.py <파일경로>
  python hallucination_guard.py content/posts/*.md          # 전체 검사
  python hallucination_guard.py --strict content/posts/my-post.md  # 엄격 모드

발행 파이프라인에 삽입:
  # GitHub Actions 또는 로컬 pre-commit hook에서 실행
  python hallucination_guard.py content/posts/new-post.md || exit 1
"""

import re
import sys
import os
import json
from pathlib import Path
from datetime import datetime

# ═══════════════════════════════════════════════════════
# 실존 보험사 리스트 (2026년 2월 기준)
# 출처: 금융감독원 금융회사 목록
# ⚠️ 정기적으로 업데이트 필요
# ═══════════════════════════════════════════════════════

KNOWN_INSURERS_KR = {
    # 손해보험사
    "삼성화재", "현대해상", "DB손해보험", "KB손해보험", "메리츠화재",
    "한화손해보험", "롯데손해보험", "흥국화재", "MG손해보험",
    "농협손해보험", "하나손해보험", "AXA손해보험", "ACE손해보험",
    "AIG손해보험", "더케이손해보험",
    # 생명보험사
    "삼성생명", "한화생명", "교보생명", "신한라이프", "미래에셋생명",
    "NH농협생명", "동양생명", "ABL생명", "라이나생명", "처브라이프",
    "AIA생명", "푸본현대생명", "카디프생명", "BNP파리바카디프",
    "KDB생명", "하나생명", "iM라이프", "DB생명",
    "오렌지라이프", "흥국생명", "DGB생명",
    # 약칭
    "삼성", "현대해상", "DB손보", "KB손보", "메리츠", "한화",
    "교보", "신한", "NH농협", "동양", "라이나", "AIA",
}

KNOWN_INSURERS_US = {
    # P&C (Auto/Home)
    "State Farm", "Geico", "Progressive", "Allstate", "USAA",
    "Liberty Mutual", "Nationwide", "Farmers", "American Family",
    "Travelers", "Erie Insurance", "Auto-Owners", "Hartford",
    "Chubb", "Cincinnati Financial",
    # Life
    "MetLife", "Prudential", "New York Life", "Northwestern Mutual",
    "MassMutual", "Lincoln Financial", "Principal Financial",
    "Transamerica", "Aflac", "Guardian Life", "Pacific Life",
    # Health
    "UnitedHealthcare", "Anthem", "Cigna", "Aetna", "Humana",
    "Kaiser Permanente", "Blue Cross Blue Shield", "BCBS",
    "Centene", "Molina Healthcare",
}

# ═══════════════════════════════════════════════════════
# 위험 표현 패턴
# ═══════════════════════════════════════════════════════

RED_FLAG_PHRASES_KR = [
    "100% 보장", "무조건 지급", "반드시 받을 수 있",
    "모든 보험사가", "전 보험사 공통", "예외 없이",
    "절대 거절되지 않", "무조건 가입 가능", "심사 없이",
    "누구나 가입", "무심사", "100% 승인",
]

RED_FLAG_PHRASES_US = [
    "guaranteed approval", "always pays out", "100% coverage",
    "no exceptions", "every insurance company", "never denied",
    "zero deductible guaranteed", "absolutely free",
    "no medical exam required for all",  # 일부 상품은 가능하지만 "모든" 상품은 아님
]

# ═══════════════════════════════════════════════════════
# 출처 키워드 (통계 인용 시 이 중 하나가 있어야 함)
# ═══════════════════════════════════════════════════════

SOURCE_KEYWORDS_KR = [
    "에 따르면", "기준", "통계", "조사", "발표", "보고서",
    "금융감독원", "보험개발원", "통계청", "한국은행",
    "보험연구원", "생명보험협회", "손해보험협회",
    "국민건강보험공단", "건강보험심사평가원",
]

SOURCE_KEYWORDS_US = [
    "according to", "survey", "data", "report", "source",
    "NAIC", "Bureau of Labor Statistics", "Census Bureau",
    "Federal Reserve", "IIHS", "J.D. Power", "AM Best",
    "Consumer Reports", "Pew Research",
]


class HallucinationGuard:
    def __init__(self, filepath, strict=False):
        self.filepath = filepath
        self.strict = strict
        self.warnings = []
        self.errors = []
        self.content = ""
        self.frontmatter = ""
        self.body = ""
        self.lang = "ko"  # default

    def load(self):
        with open(self.filepath, 'r', encoding='utf-8') as f:
            self.content = f.read()

        # frontmatter 분리
        fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', self.content, re.DOTALL)
        if fm_match:
            self.frontmatter = fm_match.group(1)
            self.body = fm_match.group(2)
        else:
            self.body = self.content

        # 언어 감지 (한글 문자가 전체의 20% 이상이면 한국어)
        korean_chars = len(re.findall(r'[가-힣]', self.body))
        total_alpha = len(re.findall(r'[a-zA-Z가-힣]', self.body))
        if total_alpha > 0 and (korean_chars / total_alpha) > 0.15:
            self.lang = "ko"
        else:
            self.lang = "en"

    def check_insurer_names(self):
        """보험사명 실존 여부 검증"""
        # 일반 보험 용어 (보험사가 아닌 보험 종류)
        INSURANCE_TERMS_KR = {
            "암보험", "실손보험", "자동차보험", "화재보험", "건강보험",
            "생명보험", "손해보험", "종신보험", "정기보험", "연금보험",
            "어린이보험", "태아보험", "운전자보험", "여행자보험", "치아보험",
            "실비보험", "간병보험", "유병자보험", "저축보험", "변액보험",
            "보장성보험", "상해보험", "배상책임보험", "재물보험",
            "실손의료보험", "의무보험", "독립보험", "통합보험",
            "다이렉트보험", "소액보험", "미니보험", "반려동물보험",
            "임베디드보험", "인슈어테크", "재보험", "공제보험",
            "책임보험", "종합보험", "펫보험", "골프보험",
            "임대보증보험", "이륜차보험", "해외여행보험",
        }

        if self.lang == "ko":
            mentions = re.findall(r'[가-힣A-Z]+(?:화재|생명|손해보험|라이프|보험)', self.body)
            known = KNOWN_INSURERS_KR
            for name in set(mentions):
                name_clean = name.strip()
                if name_clean in INSURANCE_TERMS_KR:
                    continue  # 일반 보험 용어는 스킵
                if not any(k in name_clean or name_clean in k for k in known):
                    self.warnings.append(
                        f"⚠️ 미확인 보험사명: '{name_clean}' — 금감원/NAIC 목록에서 확인 필요"
                    )
        else:
            # 미국 보험사명 패턴
            mentions = re.findall(
                r'(?:[A-Z][a-z]+ ){1,3}(?:Insurance|Life|Financial|Mutual|Healthcare)',
                self.body
            )
            known = KNOWN_INSURERS_US
            for name in set(mentions):
                name_clean = name.strip()
                if not any(k in name_clean or name_clean in k for k in known):
                    self.warnings.append(
                        f"⚠️ 미확인 보험사명(US): '{name_clean}' — NAIC 목록에서 확인 필요"
                    )

    def check_red_flags(self):
        """과장/허위 표현 감지"""
        phrases = RED_FLAG_PHRASES_KR if self.lang == "ko" else RED_FLAG_PHRASES_US
        for phrase in phrases:
            if phrase.lower() in self.body.lower():
                self.errors.append(
                    f"🚨 과장 표현 감지: '{phrase}' — 수정 필수"
                )

    def check_premium_ranges(self):
        """보험료 범위 현실성 검증"""
        if self.lang == "ko":
            # 월 보험료 (한국: 5,000원 ~ 500,000원)
            premiums = re.findall(r'월\s*(?:약\s*)?(\d{1,3}(?:,\d{3})*)원', self.body)
            for p in premiums:
                amount = int(p.replace(',', ''))
                if amount < 5000:
                    self.warnings.append(f"⚠️ 비현실적 보험료(너무 낮음): 월 {p}원")
                elif amount > 500000:
                    self.warnings.append(f"⚠️ 비현실적 보험료(너무 높음): 월 {p}원")
        else:
            # 월 보험료 (미국: $10 ~ $5,000)
            premiums = re.findall(r'\$(\d{1,3}(?:,\d{3})*)\s*/?\s*(?:month|mo|monthly)', self.body, re.I)
            for p in premiums:
                amount = int(p.replace(',', ''))
                if amount < 10:
                    self.warnings.append(f"⚠️ Unrealistic premium (too low): ${p}/month")
                elif amount > 5000:
                    self.warnings.append(f"⚠️ Unrealistic premium (too high): ${p}/month")

    def check_unsourced_stats(self):
        """출처 없는 통계 감지"""
        source_kw = SOURCE_KEYWORDS_KR if self.lang == "ko" else SOURCE_KEYWORDS_US
        lines = self.body.split('\n')

        for i, line in enumerate(lines, 1):
            # 퍼센트 수치가 있는 줄
            if re.search(r'\d+(?:\.\d+)?%', line):
                has_source = any(kw in line for kw in source_kw)
                # 이전/다음 줄에 출처가 있을 수도 있음
                context = ""
                if i > 1:
                    context += lines[i-2]
                if i < len(lines):
                    context += lines[i-1] if i-1 < len(lines) else ""
                has_source = has_source or any(kw in context for kw in source_kw)

                if not has_source:
                    snippet = line.strip()[:100]
                    if self.strict:
                        self.errors.append(
                            f"🚨 [L{i}] 출처 미명시 통계: {snippet}..."
                        )
                    else:
                        self.warnings.append(
                            f"⚠️ [L{i}] 출처 확인 필요: {snippet}..."
                        )

    def check_phone_numbers(self):
        """전화번호 형식 검증"""
        if self.lang == "ko":
            phones = re.findall(r'(\d{2,4}-\d{3,4}-\d{4})', self.body)
            for phone in phones:
                # 1588, 1577 등 대표번호 또는 02, 031 등 지역번호 확인
                if not re.match(r'^(1\d{3}|0\d{1,2})-', phone):
                    self.warnings.append(f"⚠️ 의심스러운 전화번호: {phone}")
        else:
            phones = re.findall(r'(\(\d{3}\)\s*\d{3}-\d{4}|\d{3}-\d{3}-\d{4})', self.body)
            # 미국 전화번호는 형식만 체크

    def check_word_count(self):
        """글자수/단어수 체크"""
        text_only = re.sub(r'[#*\[\]()|\-`>{}]', '', self.body)
        text_only = re.sub(r'!\[.*?\]\(.*?\)', '', text_only)  # 이미지 마크다운 제거
        text_only = re.sub(r'\[.*?\]\(.*?\)', '', text_only)    # 링크 마크다운 제거

        if self.lang == "ko":
            char_count = len(re.sub(r'\s', '', text_only))
            if char_count < 3000:
                self.warnings.append(f"⚠️ 글자수 부족: {char_count}자 (최소 3,000자)")
        else:
            word_count = len(text_only.split())
            if word_count < 1500:
                self.warnings.append(f"⚠️ Word count low: {word_count} words (minimum 1,500)")

    def check_internal_links(self):
        """내부 링크 수 체크"""
        internal_links = re.findall(r'\[.*?\]\(/posts/.*?\)', self.body)
        if len(internal_links) < 3:
            self.warnings.append(
                f"⚠️ 내부 링크 부족: {len(internal_links)}개 (최소 3개)"
            )

    def check_faq_count(self):
        """FAQ 수 체크"""
        faq_patterns = [
            len(re.findall(r'#{2,3}\s*(?:Q\d|질문|FAQ)', self.body, re.I)),
            len(re.findall(r'\*\*Q[\d:]', self.body)),
            len(re.findall(r'#{2,3}\s*.*\?', self.body)),  # 질문형 H2/H3
        ]
        max_faq = max(faq_patterns)
        if max_faq < 5:
            self.warnings.append(
                f"⚠️ FAQ 부족: 약 {max_faq}개 감지 (최소 5개)"
            )

    def check_frontmatter(self):
        """frontmatter 필수 필드 체크"""
        required_fields = ['title', 'description', 'date', 'tags']
        for field in required_fields:
            if field + ':' not in self.frontmatter.lower():
                self.errors.append(f"🚨 frontmatter 누락: {field}")

        # description 길이 체크
        desc_match = re.search(r'description:\s*["\']?(.*?)["\']?\s*$', self.frontmatter, re.M)
        if desc_match:
            desc = desc_match.group(1)
            if self.lang == "ko" and len(desc) > 150:
                self.warnings.append(f"⚠️ description 초과: {len(desc)}자 (150자 이내)")
            elif self.lang == "en" and len(desc) > 160:
                self.warnings.append(f"⚠️ description too long: {len(desc)} chars (max 160)")

    def check_consistency(self):
        """본문 내 수치 일관성 체크"""
        # 같은 항목에 대해 다른 수치가 나오면 경고
        # 예: "월 32,000원" 이 본문에서 나중에 "월 35,000원"으로 바뀌면
        # (간단한 휴리스틱 — 동일 키워드 뒤의 다른 금액)
        amount_contexts = re.findall(
            r'([\w가-힣]{2,10})\s*(?:월\s*)?(\d{1,3}(?:,\d{3})*)\s*원',
            self.body
        )
        context_amounts = {}
        for ctx, amount in amount_contexts:
            if ctx in context_amounts and context_amounts[ctx] != amount:
                self.warnings.append(
                    f"⚠️ 수치 불일치: '{ctx}' → {context_amounts[ctx]}원 vs {amount}원"
                )
            context_amounts[ctx] = amount

    def run(self):
        """전체 검증 실행"""
        self.load()
        self.check_frontmatter()
        self.check_insurer_names()
        self.check_red_flags()
        self.check_premium_ranges()
        self.check_unsourced_stats()
        self.check_phone_numbers()
        self.check_word_count()
        self.check_internal_links()
        self.check_faq_count()
        self.check_consistency()

        return self.report()

    def report(self):
        """결과 리포트 출력"""
        total_issues = len(self.errors) + len(self.warnings)

        print(f"\n{'═'*60}")
        print(f"🔍 Hallucination Guardrail v1.0")
        print(f"   파일: {self.filepath}")
        print(f"   언어: {'한국어' if self.lang == 'ko' else 'English'}")
        print(f"   모드: {'STRICT' if self.strict else 'NORMAL'}")
        print(f"{'═'*60}")

        if self.errors:
            print(f"\n🚨 ERRORS ({len(self.errors)}) — 발행 차단:")
            for e in self.errors:
                print(f"  {e}")

        if self.warnings:
            print(f"\n⚠️ WARNINGS ({len(self.warnings)}) — 확인 권장:")
            for w in self.warnings:
                print(f"  {w}")

        if total_issues == 0:
            print(f"\n✅ PASS — Hallucination 미감지. 발행 가능.")
        else:
            status = "BLOCKED" if self.errors else "REVIEW"
            print(f"\n{'🚫 BLOCKED' if self.errors else '⚠️ REVIEW'}")
            print(f"  에러: {len(self.errors)}건 | 경고: {len(self.warnings)}건")

        print(f"{'═'*60}\n")

        # 에러가 있으면 False (발행 차단)
        return len(self.errors) == 0


def main():
    import argparse
    parser = argparse.ArgumentParser(description='XIVIX Hallucination Guardrail')
    parser.add_argument('files', nargs='+', help='검증할 마크다운 파일 경로')
    parser.add_argument('--strict', action='store_true', help='엄격 모드 (출처 없는 통계 = 에러)')
    parser.add_argument('--json', action='store_true', help='JSON 형식 출력')
    args = parser.parse_args()

    all_pass = True
    results = []

    for filepath in args.files:
        if not os.path.exists(filepath):
            print(f"❌ 파일 없음: {filepath}")
            all_pass = False
            continue

        guard = HallucinationGuard(filepath, strict=args.strict)
        passed = guard.run()

        if not passed:
            all_pass = False

        if args.json:
            results.append({
                "file": filepath,
                "passed": passed,
                "errors": guard.errors,
                "warnings": guard.warnings,
                "lang": guard.lang,
            })

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
