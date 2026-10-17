# 캠핑 날씨 플래너

한국관광공사 고캠핑의 캠핑장 정보와 기상청 중기예보를 한 화면에서 검색하고, 캠핑 계획을 저장하는 웹 서비스입니다.

## 프로젝트 구성

- `frontend/`: React + Vite + TypeScript 프론트엔드. Vercel 배포 대상입니다.
- `backend/`: FastAPI 서버. Render에 배포하며 고캠핑/기상청 API를 호출합니다.
- `supabase/schema.sql`: 사용자별 캠핑 계획 테이블과 Row Level Security 정책, 예보구역 매핑 테이블입니다.

브라우저는 공공데이터 API를 직접 호출하지 않습니다. 공공데이터 API 키는 FastAPI 환경변수에만 설정합니다.

## 로컬 실행

### API 서버

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

`.env`에 공공데이터포털에서 발급한 디코딩된 서비스키를 입력합니다. API 상태 확인은 `http://localhost:8000/health`, API 문서는 `http://localhost:8000/docs`에서 할 수 있습니다.

### 프론트엔드

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

기본 주소는 프론트엔드 `http://localhost:5173`, API 서버 `http://localhost:8000`입니다. `VITE_API_BASE_URL`로 API 주소를 변경할 수 있습니다.

## 환경변수

### FastAPI / Render

| 변수 | 설명 |
| --- | --- |
| `CAMPING_API_SERVICE_KEY` | 고캠핑 API 서비스키 |
| `WEATHER_API_SERVICE_KEY` | 공공데이터포털에서 기상청 중기예보와 단기예보(상세예보) 이용 신청 후 발급/승인된 서비스키 |
| `ALLOWED_ORIGINS` | 허용할 프론트엔드 오리진. 여러 주소는 쉼표로 구분. Render에는 `https://camping-weather-planner.vercel.app`을 포함해야 합니다. |

### 프론트엔드 / Vercel

| 변수 | 설명 |
| --- | --- |
| `VITE_API_BASE_URL` | 배포된 FastAPI 서버 주소 |
| `VITE_SUPABASE_URL` | Supabase 프로젝트 URL |
| `VITE_SUPABASE_ANON_KEY` | Supabase anon 공개 키 |

Supabase SQL Editor에서 `supabase/schema.sql`을 실행합니다. 이메일/비밀번호 계정으로 가입하고 이메일 확인 없이 바로 로그인하려면 **Authentication → Sign In / Providers → Email**에서 **Confirm email**을 끕니다. 앱은 로그인한 계정의 캠핑 플랜만 저장·조회하며, 가입 확인 메일을 보내지 않습니다.

## API

- `GET /api/regions`: 전국 17개 광역 시·도 검색 지역과 좌표, 기상청 예보구역 코드를 반환합니다.
- `GET /api/campgrounds?region=seoul&type=...`: 고캠핑 기본 목록을 시·도 단위로 분류해 검색합니다. 강원도 역시 강릉 주변이 아닌 도 전체를 검색합니다.
- `GET /api/weather?region=seoul&date=YYYY-MM-DD`: 해당 날짜의 예보를 반환합니다. `map_x`와 `map_y`를 함께 전달하면 오늘부터 3일 뒤까지 캠핑장 좌표 기반 상세예보를 우선 조회하고, 그 이후 날짜는 시·도 중기예보를 사용합니다.

캠핑장 검색은 고캠핑 기본 목록을 백엔드에서 수집해 지역별로 분류하며, 결과는 페이지당 최대 100건으로 제공합니다. 전체 목록은 한 시간 동안 캐시됩니다. 캠핑장을 선택하면 좌표가 있는 경우 기상청 단기예보의 5km 격자 기준으로 인근 상세예보를 보여주며, 상세예보 기간을 벗어난 4~10일 일정은 선택한 시·도의 중기예보로 표시합니다. 중기예보는 발표일 기준 3~10일 뒤 날짜만 지원합니다. 단기예보를 사용하려면 공공데이터포털에서 **기상청 단기예보 조회서비스** 이용 신청과 승인이 필요합니다. 승인된 서비스키를 Render의 `WEATHER_API_SERVICE_KEY`에 설정한 뒤 재배포하세요. API 오류는 제공기관의 오류 메시지도 함께 표시합니다.

## 배포

- Vercel 프로젝트의 Root Directory를 `frontend`로 설정합니다.
- Render Web Service의 Root Directory는 `backend`, Build Command는 `pip install -r requirements.txt`, Start Command는 `uvicorn app.main:app --host 0.0.0.0 --port $PORT`로 설정합니다.
- Render의 `ALLOWED_ORIGINS`에는 배포된 Vercel 도메인을 입력합니다.
