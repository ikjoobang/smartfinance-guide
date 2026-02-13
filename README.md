# 🚀 Smart Finance Guide - XIVIX Blog

> Hugo 정적사이트 + Cloudflare Pages 자동 배포
> SEO + AEO + GEO 4중 최적화 AdSense 수익 블로그

## 📊 프로젝트 현황

| 항목 | 상태 |
|------|------|
| Hugo 사이트 | ✅ 빌드 성공 (94 pages, 206ms) |
| 테마 | ✅ xivix-adsense (커스텀) |
| SEO 최적화 | ✅ 메타태그, OG, Twitter Card |
| AEO 최적화 | ✅ Schema.org (Article, FAQ, HowTo, Breadcrumb) |
| GEO 최적화 | ✅ llms.txt, AI크롤러 허용, 모듈형 콘텐츠 |
| AdSense 준비 | ✅ 자동광고 + 인아티클 + 사이드바 |
| GA4 준비 | ✅ gtag.js 삽입 |
| CI/CD | ✅ GitHub Actions → Cloudflare Pages |
| 콘텐츠 | ✅ 7개 고CPC 포스트 |

## 🔧 배포 순서 (5단계)

### Step 1: GitHub Repository 생성

```bash
# GitHub에서 새 repo 생성: smartfinance-guide (Private)
# https://github.com/new

# 로컬에서 초기화 & 푸시
cd xivix-blog
git init
git add .
git commit -m "Initial commit: Hugo blog with SEO/AEO/GEO optimization"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/smartfinance-guide.git
git push -u origin main
```

### Step 2: Cloudflare Pages 연결

1. [Cloudflare Dashboard](https://dash.cloudflare.com/) 로그인
2. **Workers & Pages** → **Create application** → **Pages** → **Connect to Git**
3. GitHub 계정 연결 → `smartfinance-guide` 레포 선택
4. 빌드 설정:
   - **Framework preset**: Hugo
   - **Build command**: `hugo --minify`
   - **Build output directory**: `public`
   - **Environment variable**: `HUGO_VERSION` = `0.139.0`
5. **Save and Deploy** 클릭

> 배포 완료 시 `https://smartfinance-guide.pages.dev` 에서 접속 가능

### Step 3: 커스텀 도메인 연결

1. `smartfinance.guide` 도메인 구매 (Cloudflare Registrar 또는 Namecheap)
2. Cloudflare Pages → Custom domains → `smartfinance.guide` 추가
3. DNS 자동 설정됨 (Cloudflare에서 도메인 관리 시)

### Step 4: AdSense 설정

1. [Google AdSense](https://adsense.google.com/) 신청
2. 사이트 추가: `smartfinance.guide`
3. 승인 코드를 `hugo.toml`의 `adsensePublisher`에 입력
4. 승인 후 광고 슬롯 ID를 각 ad partial에 입력:
   - `layouts/partials/ad-in-article.html` → `data-ad-slot`
   - `layouts/partials/ad-sidebar.html` → `data-ad-slot`

### Step 5: Google Analytics 설정

1. [GA4](https://analytics.google.com/) 속성 생성
2. 측정 ID (G-XXXXXXXXXX)를 `hugo.toml`의 `googleAnalytics`에 입력
3. [Google Search Console](https://search.google.com/search-console) 등록
4. sitemap 제출: `https://smartfinance.guide/sitemap.xml`

## 📝 새 글 작성법

```bash
# 새 포스트 생성
hugo new posts/new-article-title.md

# 초안 작성 후 draft: false로 변경

# 로컬 미리보기
hugo server -D

# 배포 (git push만 하면 자동 배포)
git add .
git commit -m "Add new post: article title"
git push
```

## 📁 프로젝트 구조

```
xivix-blog/
├── .github/workflows/deploy.yml  # CI/CD (Cloudflare Pages)
├── archetypes/posts.md            # 포스트 템플릿
├── content/
│   ├── posts/                     # 블로그 포스트 (7개)
│   │   ├── best-cheap-car-insurance-2026.md      (CPC $40+)
│   │   ├── how-much-life-insurance-do-you-need.md (CPC $30+)
│   │   ├── best-personal-loans-2026.md            (CPC $15-25)
│   │   ├── chatgpt-vs-claude-vs-gemini-2026.md    (CPC $4-18)
│   │   ├── best-vpn-services-2026.md              (CPC $8-15)
│   │   ├── best-home-insurance-2026.md            (CPC $25+)
│   │   └── how-to-check-credit-score-free.md      (CPC $10-20)
│   └── pages/                     # 정적 페이지
│       ├── about.md               # E-E-A-T 신호
│       └── privacy-policy.md      # AdSense 필수
├── hugo.toml                      # 사이트 설정
├── layouts/robots.txt             # AI 크롤러 허용
├── static/
│   ├── _headers                   # Cloudflare 캐싱/보안
│   └── llms.txt                   # GEO 최적화
└── themes/xivix-adsense/          # 커스텀 테마
    ├── layouts/
    │   ├── _default/
    │   │   ├── baseof.html        # 기본 레이아웃
    │   │   ├── single.html        # 포스트 (TOC+FAQ+관련글)
    │   │   └── list.html          # 목록 페이지
    │   ├── partials/
    │   │   ├── head.html          # SEO 메타태그 전체
    │   │   ├── schema.html        # JSON-LD 구조화 데이터
    │   │   ├── header.html        # 네비게이션
    │   │   ├── footer.html        # 푸터
    │   │   ├── ad-in-article.html # 인아티클 광고
    │   │   └── ad-sidebar.html    # 사이드바 광고
    │   └── index.html             # 홈페이지
    └── static/
        ├── css/style.css          # Core Web Vitals 최적화 CSS
        └── js/main.js             # 읽기 진행률 + UX

## 🎯 수익 예상 타임라인

| 기간 | 월 트래픽 | AdSense 예상 | 총 수익 (CPA 포함) |
|------|-----------|-------------|-------------------|
| 0-3개월 | 5K | $50-100 | $100-200 |
| 3-6개월 | 30K | $300-600 | $600-1,200 |
| 6-12개월 | 100K | $1K-3K | $2K-6K |
| 12-18개월 | 300K | $3K-10K | $6K-20K |

## ⚡ 다음 단계 (TODO)

- [ ] GitHub repo 생성 & push
- [ ] Cloudflare Pages 연결
- [ ] 도메인 구매 & 연결
- [ ] AdSense 신청
- [ ] GA4 + Search Console 설정
- [ ] 주 3-5개 포스트 추가
- [ ] 이미지 최적화 (WebP)
- [ ] 뉴스레터 서비스 연동 (Buttondown/ConvertKit)
```

---

**Built by XIVIX** | Powered by Hugo + Cloudflare Pages
