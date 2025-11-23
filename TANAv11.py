import streamlit as st
import pandas as pd
import numpy as np
import math
import textwrap

# 페이지 설정
st.set_page_config(page_title="TANA", page_icon="🚦", layout="centered")

# --------------------------------------------------
# 🎨 CSS 스타일 (Final Fix: 헤더 여백 & 입력창 디자인)
# --------------------------------------------------
st.markdown("""
<style>
    @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.8/dist/web/static/pretendard.css");
    
    /* 전체 설정 */
    .stApp {
        background-color: #F2F2F7 !important;
        font-family: 'Pretendard', sans-serif;
    }
    
    /* [FIX 1] 상단 여백 대폭 추가 (잘림 방지) */
    .block-container {
        padding-top: 4rem !important; /* 2rem -> 4rem */
        padding-bottom: 5rem !important;
    }
    
    /* 헤더 */
    .app-header {
        display: flex; justify-content: space-between; align-items: center;
        margin-bottom: 15px;
    }
    .app-logo { font-size: 28px; font-weight: 900; color: #1C1C1E; letter-spacing: -1px; }
    .weather-pill { 
        background: white; padding: 6px 14px; border-radius: 20px; 
        font-size: 13px; font-weight: 700; color: #1C1C1E;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

    /* 광고 배너 */
    .ad-banner {
        background: #e9ecef; 
        border: 1px dashed #adb5bd;
        border-radius: 16px; padding: 12px; margin-bottom: 25px;
        text-align: center; font-size: 13px; color: #495057;
        display: flex; align-items: center; justify-content: center; gap: 10px;
    }
    .ad-tag {
        background: #ced4da; color: white; font-size: 10px; font-weight: bold;
        padding: 2px 6px; border-radius: 4px;
    }

    /* [FIX 3] 입력창(Selectbox) 디자인 커스텀 - 흰색 배경 & 잘 보이게 */
    /* 셀렉트박스 전체 컨테이너 */
    [data-testid="stSelectbox"] {
        margin-bottom: 10px;
    }
    /* 라벨 (출발 정류장 등) */
    .stSelectbox label p { 
        font-size: 12px !important; font-weight: 700 !important; color: #8E8E93 !important; 
        margin-bottom: 4px;
    }
    /* 클릭 박스 (배경 흰색으로 강제) */
    div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border: 1px solid #E5E5EA !important;
        border-radius: 16px !important;
        color: #1C1C1E !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02) !important;
        padding-left: 5px;
    }
    /* 선택된 텍스트 */
    div[data-baseweb="select"] span {
        color: #1C1C1E !important; font-weight: 600;
    }
    /* 드롭다운 아이콘 */
    div[data-baseweb="select"] svg {
        fill: #8E8E93 !important;
    }

    /* 액션 카드 (Hero) */
    .hero-card {
        border-radius: 26px; padding: 40px 20px 60px 20px;
        text-align: center; color: white; margin-bottom: 20px;
        box-shadow: 0 15px 35px rgba(0,0,0,0.15);
        position: relative; overflow: hidden;
        animation: pulse 2s infinite ease-in-out;
    }
    .hero-green { background: linear-gradient(135deg, #34C759, #30B0C7); }
    .hero-yellow { background: linear-gradient(135deg, #FFCC00 0%, #FF9500 100%); text-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .hero-red { background: linear-gradient(135deg, #FF453A, #FF375F); }
    .hero-blue { background: linear-gradient(135deg, #007AFF, #5AC8FA); }

    .hero-icon { font-size: 48px; display: block; margin-bottom: 10px; line-height: 1; }
    .hero-title { font-size: 36px; font-weight: 800; margin: 0; line-height: 1.2; }
    .hero-sub { font-size: 16px; font-weight: 600; margin-top: 8px; opacity: 0.95; }

    /* Hero 내부 미니 트래킹 바 */
    .hero-progress-area {
        position: absolute; bottom: 25px; left: 25px; right: 25px;
        height: 20px; display: flex; align-items: center;
    }
    .mini-track-bg {
        width: 100%; height: 6px; background: rgba(255,255,255,0.3); border-radius: 3px; position: relative;
    }
    .mini-track-fill {
        height: 100%; background: white; border-radius: 3px; transition: width 0.3s ease;
        box-shadow: 0 0 10px rgba(255,255,255,0.5);
    }
    .mini-avatar {
        position: absolute; top: 50%; transform: translate(-50%, -50%);
        font-size: 24px; transition: left 0.3s ease; z-index: 10;
        text-shadow: 0 2px 5px rgba(0,0,0,0.2); margin-top: -3px;
    }
    .mini-text {
        position: absolute; bottom: -22px; width: 100%; text-align: center;
        font-size: 11px; color: rgba(255,255,255,0.9); font-weight: 700; letter-spacing: 0.5px;
    }

    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.005); }
        100% { transform: scale(1); }
    }

    /* 정보 그리드 (CSS Grid) */
    .info-grid-container {
        display: grid; grid-template-columns: 1fr 1fr; gap: 15px; width: 100%;
    }
    .grid-card {
        background: white; border-radius: 20px; padding: 20px 10px; text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03); 
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        height: 100%;
    }
    .grid-label { font-size: 12px; color: #8E8E93; font-weight: 700; margin-bottom: 6px; }
    .grid-value { font-size: 22px; color: #1C1C1E; font-weight: 800; letter-spacing: -0.5px; }
    .grid-sub { font-size: 11px; color: #AEAEB2; margin-top: 4px; font-weight: 500; }
    
    .txt-red { color: #FF453A !important; }
    .txt-blue { color: #007AFF !important; }
    .txt-green { color: #34C759 !important; }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# 📍 데이터 & 함수
# --------------------------------------------------
USER_ORIGIN = [37.3835, 126.6550]
station_db = {
    "연세대학교": {"coords": [37.3815, 126.6580], "buses": ["M6724", "9201"]},
    "박문여고": {"coords": [37.3948, 126.6672], "buses": ["순환41", "9"]},
    "박문중": {"coords": [37.3932, 126.6682], "buses": ["순환41"]}
}

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def interpolate_pos(start, end, progress):
    lat = start[0] + (end[0] - start[0]) * progress
    lon = start[1] + (end[1] - start[1]) * progress
    return [lat, lon]

# --------------------------------------------------
# 🔧 Admin Console
# --------------------------------------------------
with st.sidebar:
    st.header("🎬 Director Mode")
    
    weather = st.radio("날씨 설정", ["☀️ 맑음", "🌧️ 비", "❄️ 눈"], horizontal=True)
    journey_progress = st.slider("진행률 (%)", 0, 100, 0)
    admin_speed = st.slider("속도 (km/h)", 2.0, 15.0, 5.0)
    admin_time_passed = st.slider("버스 경과 (분)", 0, 60, 25)
    admin_seats = st.slider("잔여 좌석 (석)", 0, 45, 4)
    prev_bus_status = st.radio("상태", ["🟢 빈 자리", "🔴 만석"], index=0)

# --------------------------------------------------
# 🖥️ 메인 로직
# --------------------------------------------------
weather_icon = weather.split(" ")[0]

# [1] 헤더
st.markdown(f"""
<div class="app-header">
    <div class="app-logo">TANA</div>
    <div class="weather-pill">{weather_icon} 18°C</div>
</div>
""", unsafe_allow_html=True)

# [2] 광고 배너
st.markdown("""
<div class="ad-banner">
    <span class="ad-tag">AD</span>
    <span><b>스타벅스</b> : 버스 기다릴 땐 따뜻한 라떼 한 잔 ☕️</span>
</div>
""", unsafe_allow_html=True)

# [3] 사용자 입력 (투명 박스 제거됨 -> 위젯 자체 스타일링 적용)
# [FIX 2] 이상한 흰색 빈칸 사라짐
c1, c2 = st.columns(2)
with c1:
    target_station = st.selectbox("출발 정류장", list(station_db.keys()))
with c2:
    target_bus = st.selectbox("탑승 버스", station_db[target_station]["buses"])

# --- 로직 계산 ---
origin = USER_ORIGIN
dest = station_db[target_station]["coords"]
curr_pos = interpolate_pos(origin, dest, journey_progress / 100)
dist_km = calculate_distance(curr_pos[0], curr_pos[1], dest[0], dest[1])

resist = 1.0
if "🌧️" in weather: resist = 0.8
elif "❄️" in weather: resist = 0.7
real_speed = admin_speed * resist

req_time = 0 if dist_km < 0.02 else (dist_km / real_speed) * 60

base_queue = 0 if "빈 자리" in prev_bus_status else 25
q_future = base_queue + int(admin_time_passed * 0.5) + (0.5 * req_time)
bus_eta = 15

# 상태 결정
if journey_progress >= 100:
    theme, icon, title, sub = "hero-blue", "🏁", "도착 완료", "수고하셨습니다!"
elif req_time > bus_eta:
    theme, icon, title, sub = "hero-red", "🚫", "탑승 불가", f"버스 {bus_eta}분 전 도착"
elif q_future > admin_seats:
    theme, icon, title, sub = "hero-red", "😱", "포기해", f"대기 {int(q_future)}명 (만석)"
elif q_future > (admin_seats - 5):
    theme, icon, title, sub = "hero-yellow", "🏃", "지금 뛰어!", f"막차 가능성 ({int(admin_seats)}석)"
else:
    theme, icon, title, sub = "hero-green", "☕️", "여유 있음", "천천히 걸어가세요"

# [4] 액션 카드 (Hero)
avatar = '🚀' if real_speed > 10 else ('🏃' if real_speed > 6 else '🚶')

st.markdown(f"""
<div class="hero-card {theme}">
<span class="hero-icon">{icon}</span>
<h1 class="hero-title">{title}</h1>
<div class="hero-sub">{sub}</div>
<div class="hero-progress-area">
<div class="mini-track-bg"><div class="mini-track-fill" style="width: {journey_progress}%;"></div></div>
<div class="mini-avatar" style="left: {journey_progress}%;">{avatar}</div>
<div class="mini-text">{int(dist_km*1000)}m 남음</div>
</div>
</div>
""", unsafe_allow_html=True)

# [5] 정보 그리드
seat_cls = "txt-red" if admin_seats < 5 else "txt-green"

def get_min_sec(t):
    m = int(t)
    s = int((t - m) * 60)
    return f"{m}분 {s}초"

st.markdown(f"""
<div class="info-grid-container">
<div class="grid-card">
<div class="grid-label">👥 대기 인원</div>
<div class="grid-value">{int(q_future)}명</div>
<div class="grid-sub">현재 {int(base_queue + admin_time_passed*0.5)}명</div>
</div>
<div class="grid-card">
<div class="grid-label">🚌 버스 도착까지</div>
<div class="grid-value">{bus_eta}분</div>
<div class="grid-sub">{target_bus}</div>
</div>
<div class="grid-card">
<div class="grid-label">💺 잔여 좌석</div>
<div class="grid-value {seat_cls}">{admin_seats}석</div>
<div class="grid-sub">여유 {admin_seats-5 if admin_seats>5 else 0}석</div>
</div>
<div class="grid-card">
<div class="grid-label">⏱ 예상 소요시간</div>
<div class="grid-value">{get_min_sec(req_time)}</div>
<div class="grid-sub">속도 {real_speed:.1f}km/h</div>
</div>
</div>
""", unsafe_allow_html=True)
