import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import {
  ArrowDownUp,
  ArrowRight,
  Bookmark,
  CalendarDays,
  Check,
  ChevronDown,
  CloudSun,
  Compass,
  Droplets,
  Heart,
  Leaf,
  LoaderCircle,
  MapPin,
  Mountain,
  PawPrint,
  Search,
  Sun,
  TentTree,
  Thermometer,
  Wind,
  X,
} from "lucide-react";
import { getCampgrounds, getRegions, getWeather } from "./lib/api";
import { supabase } from "./lib/supabase";
import type { Campground, Region, SavedPlan, WeatherForecast } from "./types";

const typeOptions = ["전체", "일반야영장", "자동차야영장", "글램핑", "카라반"];
const fallbackRegions: Pick<Region, "id" | "name">[] = [
  { id: "seoul", name: "서울" },
  { id: "gangneung", name: "강원 강릉" },
  { id: "daejeon", name: "대전" },
  { id: "gwangju", name: "광주" },
  { id: "daegu", name: "대구" },
  { id: "busan", name: "부산" },
  { id: "jeju", name: "제주" },
];

function localDate(offset: number): string {
  const date = new Date();
  date.setDate(date.getDate() + offset);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function App() {
  const [regions, setRegions] =
    useState<Pick<Region, "id" | "name">[]>(fallbackRegions);
  const [regionId, setRegionId] = useState("seoul");
  const [date, setDate] = useState(localDate(4));
  const [campType, setCampType] = useState("전체");
  const [campgrounds, setCampgrounds] = useState<Campground[]>([]);
  const [weather, setWeather] = useState<WeatherForecast | null>(null);
  const [selectedCamp, setSelectedCamp] = useState<Campground | null>(null);
  const [savedPlans, setSavedPlans] = useState<SavedPlan[]>([]);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [authOpen, setAuthOpen] = useState(false);
  const [authMode, setAuthMode] = useState<"signIn" | "signUp">("signIn");
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState("");
  const [authSuccess, setAuthSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [activeTab, setActiveTab] = useState<"discover" | "saved">("discover");

  const region = useMemo(
    () => regions.find((item) => item.id === regionId),
    [regions, regionId],
  );

  useEffect(() => {
    getRegions()
      .then((data) => setRegions(data))
      .catch((reason: Error) => {
        setError(
          `지역 목록 API에 연결하지 못해 기본 지역 목록을 표시합니다. 검색하려면 Render의 ALLOWED_ORIGINS에 현재 웹 주소를 추가해 주세요. (${reason.message})`,
        );
      });
  }, []);

  useEffect(() => {
    if (!supabase) {
      const stored = localStorage.getItem("camp-on-plans");
      if (stored) {
        try {
          setSavedPlans(JSON.parse(stored) as SavedPlan[]);
        } catch {
          setError("저장된 캠핑 플랜을 읽지 못했습니다. 브라우저 저장 데이터를 확인해 주세요.");
        }
      }
      return;
    }

    supabase.auth.getSession().then(({ data, error: authError }) => {
      if (authError) setError(authError.message);
      setUserEmail(data.session?.user.email ?? null);
    });
    const { data } = supabase.auth.onAuthStateChange((_event, session) => {
      setUserEmail(session?.user.email ?? null);
    });
    return () => data.subscription.unsubscribe();
  }, []);

  async function search() {
    setLoading(true);
    setError("");
    setNotice("");
    setWeather(null);
    try {
      const [campResult, weatherResult] = await Promise.allSettled([
        getCampgrounds(regionId, campType === "전체" ? "" : campType),
        getWeather(regionId, date),
      ]);
      if (campResult.status === "fulfilled") {
        setCampgrounds(campResult.value.items);
        setSelectedCamp(null);
      } else {
        setCampgrounds([]);
      }
      if (weatherResult.status === "fulfilled") {
        setWeather(weatherResult.value);
      }
      const failures = [campResult, weatherResult]
        .filter((result): result is PromiseRejectedResult => result.status === "rejected")
        .map((result) =>
          result.reason instanceof Error
            ? result.reason.message
            : "알 수 없는 오류가 발생했습니다.",
        );
      if (failures.length) setError(failures.join(" · "));
    } finally {
      setLoading(false);
    }
  }

  async function authenticate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAuthError("");
    setAuthSuccess("");
    if (!supabase) {
      setAuthError("계정 기능을 사용하려면 Supabase URL과 anon key를 설정해 주세요.");
      return;
    }
    if (authMode === "signUp" && password !== confirmPassword) {
      setAuthError("비밀번호 확인이 일치하지 않습니다.");
      return;
    }

    setAuthLoading(true);
    try {
      if (authMode === "signUp") {
        const { data, error: signUpError } = await supabase.auth.signUp({
          email: email.trim(),
          password,
          options: { emailRedirectTo: window.location.origin },
        });
        if (signUpError) {
          setAuthError(signUpError.message);
          return;
        }
        if (!data.session) {
          setAuthSuccess("가입 확인 메일을 보냈습니다. 메일의 링크를 눌러 계정을 활성화해 주세요.");
          setPassword("");
          setConfirmPassword("");
          return;
        }
        setNotice("회원가입과 로그인이 완료되었습니다.");
      } else {
        const { error: signInError } = await supabase.auth.signInWithPassword({
          email: email.trim(),
          password,
        });
        if (signInError) {
          setAuthError(signInError.message);
          return;
        }
        setNotice("로그인되었습니다.");
      }
      setAuthOpen(false);
      setPassword("");
      setConfirmPassword("");
    } catch (reason) {
      setAuthError(
        reason instanceof Error
          ? reason.message
          : "인증 요청을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.",
      );
    } finally {
      setAuthLoading(false);
    }
  }

  async function signOut() {
    if (supabase) {
      const { error: authError } = await supabase.auth.signOut();
      if (authError) setError(authError.message);
    }
  }

  async function savePlan(camp: Campground) {
    const plan: SavedPlan = { campground: camp, region: regionId, date };
    if (supabase && userEmail) {
      const { error: saveError } = await supabase.from("camping_plans").upsert({
        campground_id: camp.content_id,
        campground_name: camp.name,
        campground_address: camp.address,
        region_id: regionId,
        plan_date: date,
        campground_data: camp,
      }, { onConflict: "user_id,campground_id,plan_date" });
      if (saveError) {
        setError(saveError.message);
        return;
      }
      setNotice("캠핑 계획을 Supabase에 저장했습니다.");
      await loadSavedPlans();
      return;
    }

    const nextPlans = [
      plan,
      ...savedPlans.filter(
        (item) =>
          item.campground.content_id !== camp.content_id || item.date !== date,
      ),
    ];
    setSavedPlans(nextPlans);
    localStorage.setItem("camp-on-plans", JSON.stringify(nextPlans));
    setNotice("캠핑 계획을 이 브라우저에 저장했습니다.");
  }

  function toggleSavedPlan(camp: Campground) {
    const savedPlan = savedPlans.find(
      (item) =>
        item.campground.content_id === camp.content_id && item.date === date,
    );
    if (savedPlan) {
      void removePlan(savedPlan);
    } else {
      void savePlan(camp);
    }
  }

  async function loadSavedPlans() {
    if (!supabase || !userEmail) return;
    const { data, error: loadError } = await supabase
      .from("camping_plans")
      .select("id, campground_data, region_id, plan_date, created_at")
      .order("created_at", { ascending: false });
    if (loadError) {
      setError(loadError.message);
      return;
    }
    setSavedPlans(
      (data ?? []).map((item) => ({
        id: item.id,
        campground: item.campground_data as Campground,
        region: item.region_id,
        date: item.plan_date,
        created_at: item.created_at,
      })),
    );
  }

  async function removePlan(plan: SavedPlan) {
    if (supabase && userEmail && plan.id) {
      const { error: deleteError } = await supabase
        .from("camping_plans")
        .delete()
        .eq("id", plan.id);
      if (deleteError) {
        setError(deleteError.message);
        return;
      }
      await loadSavedPlans();
      return;
    }
    const nextPlans = savedPlans.filter(
      (item) =>
        item.campground.content_id !== plan.campground.content_id ||
        item.date !== plan.date,
    );
    setSavedPlans(nextPlans);
    localStorage.setItem("camp-on-plans", JSON.stringify(nextPlans));
  }

  useEffect(() => {
    if (userEmail) void loadSavedPlans();
  }, [userEmail]);

  useEffect(() => {
    if (!authOpen) return;
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setAuthOpen(false);
    }
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [authOpen]);

  const currentWeather = weather;
  const formattedDate = new Intl.DateTimeFormat("ko-KR", {
    month: "long",
    day: "numeric",
    weekday: "short",
  }).format(new Date(`${date}T12:00:00`));

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#" aria-label="Camp On 홈">
          <span className="brand-mark"><TentTree size={22} strokeWidth={2.3} /></span>
          <span>camp<span className="brand-colon">:</span>on</span>
        </a>
        <nav className="main-nav" aria-label="주 메뉴">
          <button className={activeTab === "discover" ? "nav-link active" : "nav-link"} onClick={() => setActiveTab("discover")}>캠핑장 찾기</button>
          <button className={activeTab === "saved" ? "nav-link active" : "nav-link"} onClick={() => setActiveTab("saved")}>내 플랜 <span className="nav-count">{savedPlans.length}</span></button>
        </nav>
        <div className="account-area">
          {userEmail ? (
            <>
              <span className="account-email">{userEmail}</span>
              <button className="button button-quiet button-small" onClick={signOut}>로그아웃</button>
            </>
          ) : (
            <button className="button button-quiet button-small" onClick={() => { setAuthError(""); setAuthOpen(true); }}>
              로그인 / 회원가입 <ArrowRight size={14} />
            </button>
          )}
        </div>
      </header>

      <main>
        {activeTab === "discover" ? (
          <>
            <section className="hero">
              <div className="hero-copy">
                <div className="eyebrow"><span className="eyebrow-dot" /> YOUR NEXT OUTDOOR STORY</div>
                <h1>날씨까지 보고 고르는<br /><span>좋은 캠핑</span></h1>
                <p>캠핑장과 날씨를 한눈에 비교하고<br className="mobile-break" /> 마음에 드는 순간을 계획해 보세요.</p>
                <div className="hero-note"><Leaf size={15} /> 자연을 더 가까이, 준비는 더 가볍게</div>
              </div>
              <div className="hero-art" aria-hidden="true">
                <div className="sun-disc" />
                <div className="hill hill-back" />
                <div className="hill hill-front" />
                <div className="hero-tent"><TentTree size={100} strokeWidth={1.05} /></div>
                <div className="hero-sticker"><span>GOOD DAYS</span><strong>OUTSIDE</strong><Sun size={16} /></div>
              </div>
            </section>

            <section className="search-panel" aria-label="캠핑장 검색 조건">
              <div className="search-panel-heading">
                <div><span className="panel-kicker">PLAN YOUR TRIP</span><h2>어디로 떠나볼까요?</h2></div>
                <span className="panel-step"><span>01</span> 목적지와 일정을 선택해 주세요</span>
              </div>
              <div className="search-controls">
                <label className="control-group">
                  <span className="control-label"><MapPin size={15} /> 지역</span>
                  <span className="select-wrap"><select value={regionId} onChange={(event) => setRegionId(event.target.value)}>{regions.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}</select><ChevronDown size={15} /></span>
                </label>
                <label className="control-group date-control">
                  <span className="control-label"><CalendarDays size={15} /> 캠핑 날짜</span>
                  <input type="date" value={date} min={localDate(3)} max={localDate(10)} onChange={(event) => setDate(event.target.value)} />
                </label>
                <label className="control-group type-control">
                  <span className="control-label"><TentTree size={15} /> 캠핑 유형</span>
                  <span className="select-wrap"><select value={campType} onChange={(event) => setCampType(event.target.value)}>{typeOptions.map((type) => <option key={type}>{type}</option>)}</select><ChevronDown size={15} /></span>
                </label>
                <button className="button button-primary search-button" onClick={() => void search()} disabled={loading}>
                  {loading ? <LoaderCircle size={17} className="spin" /> : <Search size={17} />}
                  {loading ? "찾는 중" : "캠핑장 찾기"}
                </button>
              </div>
              <div className="search-foot"><span><Wind size={13} /> 기상청 중기예보 기준 3~10일 일정 검색</span><button onClick={() => { setRegionId("seoul"); setDate(localDate(4)); setCampType("전체"); }}>조건 초기화</button></div>
            </section>

            {error && <div className="message message-error" role="alert"><span>{error}</span><button onClick={() => setError("")} aria-label="오류 닫기"><X size={16} /></button></div>}
            {notice && <div className="message message-success" role="status"><Check size={16} /><span>{notice}</span><button onClick={() => setNotice("")} aria-label="안내 닫기"><X size={16} /></button></div>}

            <section className="results-section">
              <div className="section-heading">
                <div><div className="section-overline">CURATED FOR YOUR TRIP</div><h2>{campgrounds.length ? <><span>{region?.name ?? "선택 지역"}</span>에서 찾은 캠핑장</> : "오늘의 캠핑 아이디어"}</h2></div>
                <div className="result-tools">{campgrounds.length > 0 && <span className="result-count">{campgrounds.length}<small> places</small></span>}<button className="sort-button"><ArrowDownUp size={14} /> 추천순</button></div>
              </div>
              <div className="results-layout">
                <div className="camp-list">
                  {campgrounds.length > 0 ? campgrounds.map((camp, index) => (
                    <CampCard key={`${camp.content_id}-${index}`} camp={camp} selected={selectedCamp?.content_id === camp.content_id} onSelect={() => setSelectedCamp(camp)} onSave={() => toggleSavedPlan(camp)} saved={savedPlans.some((plan) => plan.campground.content_id === camp.content_id && plan.date === date)} />
                  )) : (
                    <div className="empty-state">
                      <div className="empty-icon">{loading ? <LoaderCircle size={26} className="spin" /> : <Compass size={25} />}</div>
                      <h3>{loading ? "여행 정보를 모으고 있어요" : "검색 조건을 고르면 캠핑장이 보여요"}</h3>
                      <p>{loading ? "캠핑장과 날짜별 날씨를 함께 확인하고 있습니다." : "지역과 날짜, 원하는 캠핑 유형을 선택해 보세요."}</p>
                      {!loading && <button className="button button-outline" onClick={() => void search()}>지금 검색하기 <ArrowRight size={15} /></button>}
                    </div>
                  )}
                </div>
                <aside className="weather-card">
                  <div className="weather-topline"><span className="weather-label"><CloudSun size={15} /> YOUR TRIP WEATHER</span><span className="weather-live"><i /> 기상청 예보</span></div>
                  <div className="weather-location"><MapPin size={14} /> {region?.name ?? "지역 선택"} <span>·</span> {formattedDate}</div>
                  {currentWeather ? (
                    <>
                      <div className="weather-main">
                        <div className="weather-icon">{weatherIcon(currentWeather.weather)}</div>
                        <div><strong>{currentWeather.weather}</strong><span>예보 {currentWeather.forecast_day}일 전</span></div>
                      </div>
                      <div className="temp-range"><span>{currentWeather.min_temperature ?? "—"}°</span><div className="temp-track"><i /></div><span>{currentWeather.max_temperature ?? "—"}°</span></div>
                      <div className="weather-stats">
                        <div><span><Droplets size={15} /> 강수확률</span><strong>{currentWeather.precipitation_probability ?? "—"}<small>{currentWeather.precipitation_probability === null ? "" : "%"}</small></strong></div>
                        <div><span><Thermometer size={15} /> 최저 기온</span><strong>{currentWeather.min_temperature ?? "—"}<small>°C</small></strong></div>
                        <div><span><Sun size={15} /> 최고 기온</span><strong>{currentWeather.max_temperature ?? "—"}<small>°C</small></strong></div>
                      </div>
                    </>
                  ) : (
                    <div className="weather-placeholder"><div className="cloud-illustration"><CloudSun size={50} strokeWidth={1.2} /></div><p>검색하면 선택한 날짜의<br />날씨를 알려드릴게요.</p></div>
                  )}
                  <div className="weather-foot"><span><i /> 중기예보 데이터</span><span>발표시각 기준</span></div>
                </aside>
              </div>
            </section>
            <section className="feature-strip">
              <div><span className="feature-icon green"><Mountain size={18} /></span><p><strong>캠핑장 한눈에</strong><small>시설과 유형을 비교해요</small></p></div>
              <div><span className="feature-icon yellow"><CloudSun size={18} /></span><p><strong>날씨까지 한 번에</strong><small>강수확률과 기온을 확인해요</small></p></div>
              <div><span className="feature-icon coral"><Bookmark size={18} /></span><p><strong>내 플랜에 저장</strong><small>마음에 드는 곳을 모아봐요</small></p></div>
            </section>
          </>
        ) : (
          <section className="saved-page">
            <div className="section-overline">YOUR CAMPING JOURNAL</div>
            <div className="saved-title-row"><div><h1>저장한 플랜</h1><p>마음에 담아둔 여행을 다시 꺼내보세요.</p></div><span className="saved-count">{savedPlans.length} plans</span></div>
            {savedPlans.length ? <div className="saved-grid">{savedPlans.map((plan, index) => <CampCard key={plan.id ?? `${plan.campground.content_id}-${index}`} camp={plan.campground} savedDate={plan.date} selected={false} onSelect={() => { setRegionId(plan.region); setDate(plan.date); setActiveTab("discover"); setSelectedCamp(plan.campground); }} onSave={() => void removePlan(plan)} saved />)}</div> : <div className="saved-empty"><Heart size={28} /><h2>아직 저장한 플랜이 없어요</h2><p>캠핑장 카드의 저장 버튼을 눌러 나만의 여행 목록을 만들어 보세요.</p><button className="button button-primary" onClick={() => setActiveTab("discover")}>캠핑장 둘러보기 <ArrowRight size={16} /></button></div>}
          </section>
        )}
      </main>
      <footer className="footer"><a className="brand footer-brand" href="#"><span className="brand-mark"><TentTree size={18} /></span><span>camp<span className="brand-colon">:</span>on</span></a><span>여행의 설렘은 더하고, 준비의 번거로움은 덜고.</span><span>기상청 · 한국관광공사 고캠핑 API</span></footer>
      {authOpen && (
        <div
          className="auth-backdrop"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setAuthOpen(false);
          }}
        >
          <section className="auth-dialog" role="dialog" aria-modal="true" aria-labelledby="auth-title">
            <button className="auth-close" type="button" aria-label="닫기" onClick={() => setAuthOpen(false)}>
              <X size={18} />
            </button>
            <div className="auth-mark"><TentTree size={23} /></div>
            <div className="auth-eyebrow">CAMP:ON ACCOUNT</div>
            <h2 id="auth-title">{authMode === "signUp" ? "새 계정 만들기" : "다시 오신 걸 환영해요"}</h2>
            <p className="auth-description">
              {authMode === "signUp"
                ? "계정을 만들고 캠핑 플랜을 안전하게 저장해 보세요."
                : "로그인하고 저장한 캠핑 플랜을 확인해 보세요."}
            </p>
            <form className="auth-form" onSubmit={(event) => void authenticate(event)}>
              <label>
                이메일
                <input
                  type="email"
                  autoComplete="email"
                  placeholder="name@example.com"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                />
              </label>
              <label>
                비밀번호
                <input
                  type="password"
                  autoComplete={authMode === "signUp" ? "new-password" : "current-password"}
                  placeholder="8자 이상 입력해 주세요"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  minLength={8}
                  required
                />
              </label>
              {authMode === "signUp" && (
                <label>
                  비밀번호 확인
                  <input
                    type="password"
                    autoComplete="new-password"
                    placeholder="비밀번호를 한 번 더 입력해 주세요"
                    value={confirmPassword}
                    onChange={(event) => setConfirmPassword(event.target.value)}
                    minLength={8}
                    required
                  />
                </label>
              )}
              {authError && <p className="auth-error" role="alert">{authError}</p>}
              {authSuccess && <p className="auth-success" role="status">{authSuccess}</p>}
              {!supabase && <p className="auth-config-note">계정 생성과 로그인은 Supabase 환경변수 설정 후 사용할 수 있습니다.</p>}
              <button className="button button-primary auth-submit" type="submit" disabled={authLoading}>
                {authLoading ? <LoaderCircle size={16} className="spin" /> : null}
                {authLoading
                  ? "처리 중..."
                  : authMode === "signUp"
                    ? "회원가입"
                    : "로그인"}
              </button>
            </form>
            <p className="auth-switch">
              {authMode === "signUp" ? "이미 계정이 있나요?" : "아직 계정이 없나요?"}
              <button
                type="button"
                onClick={() => {
                  setAuthMode(authMode === "signUp" ? "signIn" : "signUp");
                  setAuthError("");
                  setAuthSuccess("");
                  setConfirmPassword("");
                }}
              >
                {authMode === "signUp" ? "로그인" : "회원가입"}
              </button>
            </p>
          </section>
        </div>
      )}
    </div>
  );
}

function weatherIcon(description: string) {
  if (description.includes("비")) return <Droplets size={36} strokeWidth={1.4} />;
  if (description.includes("흐림")) return <CloudSun size={39} strokeWidth={1.3} />;
  return <Sun size={39} strokeWidth={1.3} />;
}

function CampCard({
  camp,
  selected,
  onSelect,
  onSave,
  saved = false,
  savedDate,
}: {
  camp: Campground;
  selected: boolean;
  onSelect: () => void;
  onSave: () => void;
  saved?: boolean;
  savedDate?: string;
}) {
  return (
    <article className={`camp-card${selected ? " selected" : ""}`} onClick={onSelect}>
      <div className="camp-photo" style={camp.image_url ? { backgroundImage: `url("${camp.image_url}")` } : undefined}>
        {!camp.image_url && <div className="photo-fallback"><TentTree size={38} strokeWidth={1.1} /><span>WEEKEND<br />IN NATURE</span></div>}
        <span className="camp-badge">{camp.type || "자연 속 캠핑"}</span>
        <button className={`save-button${saved ? " is-saved" : ""}`} type="button" aria-label={saved ? "플랜 저장 취소" : "플랜 저장"} aria-pressed={saved} onClick={(event) => { event.stopPropagation(); onSave(); }}><Heart size={17} fill={saved ? "currentColor" : "none"} /></button>
      </div>
      <div className="camp-info">
        <div className="camp-title-row"><h3>{camp.name}</h3><span className="rating-mark"><Leaf size={12} /> PICK</span></div>
        <div className="camp-address"><MapPin size={13} /> {camp.address || [camp.province, camp.district].filter(Boolean).join(" ") || "주소 정보 없음"}</div>
        {savedDate && <div className="saved-date"><CalendarDays size={13} /> {savedDate}</div>}
        {camp.description && <p className="camp-description">{camp.description}</p>}
        <div className="camp-tags">{camp.facilities.slice(0, 3).map((facility) => <span key={facility}>{facility}</span>)}{camp.pet_allowed && camp.pet_allowed !== "정보 없음" && <span><PawPrint size={11} /> 반려동물 {camp.pet_allowed}</span>}</div>
        <div className="camp-actions">{camp.reservation_url ? <a href={camp.reservation_url} target="_blank" rel="noreferrer" onClick={(event) => event.stopPropagation()}>예약 정보 보기 <ArrowRight size={14} /></a> : <span className="no-reservation">예약 정보 확인하기</span>}<button onClick={(event) => { event.stopPropagation(); onSelect(); }}>상세 보기</button></div>
      </div>
    </article>
  );
}

export default App;
