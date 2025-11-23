import streamlit as st
import pandas as pd
import numpy as np
import math
import base64
import textwrap

# 페이지 설정
st.set_page_config(page_title="TANA", page_icon="🚦", layout="centered")

# --------------------------------------------------
# 🎨 CSS 스타일 (지도 삭제 & 레이아웃 최적화)
# --------------------------------------------------
st.markdown("""
<style>
    @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.8/dist/web/static/pretendard.css");
    
    .main {
        background-color: #F2F2F7;
        font-family: 'Pretendard', sans-serif;
    }
    
    /* 헤더 */
    .app-header {
        display: flex; justify-content: space-between; align-items: center;
        padding: 10px 5px 15px 5px;
        margin-bottom: 10px;
    }
    .app-logo { font-size: 26px; font-weight: 900; letter-spacing: -1px; color: #1C1C1E; }
    .weather-pill { 
        background: white; padding: 8px 14px; border-radius: 20px; 
        font-size: 14px; font-weight: 700; color: #1C1C1E;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

    /* 1. 액션 카드 (Hero) - 최상단 강조 */
    .hero-card {
        border-radius: 26px; padding: 35px 20px; text-align: center; color: white; margin-bottom: 25px;
        animation: pulse 2s infinite ease-in-out;
        box-shadow: 0 15px 35px rgba(0,0,0,0.15);
        position: relative; overflow: hidden;
    }
    .hero-green { background: linear-gradient(135deg, #34C759, #30B0C7); }
    .hero-yellow { background: linear-gradient(135deg, #FF9F0A, #FF375F); }
    .hero-red { background: linear-gradient(135deg, #FF453A, #FF375F); }
    .hero-blue { background: linear-gradient(135deg, #007AFF, #5AC8FA); }

    .hero-icon { font-size: 48px; display: block; margin-bottom: 10px; }
    .hero-title { font-size: 34px; font-weight: 800; margin: 0; line-height: 1.1; }
    .hero-sub { font-size: 16px; font-weight: 600; margin-top: 8px; opacity: 0.95; }

    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.01); }
        100% { transform: scale(1); }
    }

    /* 2. 라이브 루트 (게이지) - 중간 배치 */
    .route-container {
        background: white; border-radius: 22px; padding: 25px 20px; margin-bottom: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
    }
    .route-header { 
        font-size: 13px; color: #8E8E93; font-weight: 700; margin-bottom: 30px;
        display: flex; justify-content: space-between; text-transform: uppercase;
    }
    
    .track-bg {
        width: 100%; height: 8px; background: #E5E5EA; border-radius: 4px; position: relative;
    }
    .track-fill {
        height: 100%; border-radius: 4px; transition: width 0.3s ease;
    }
    .avatar-wrapper {
        position: absolute; top: 50%; transform: translate(-50%, -50%); 
        transition: left 0.3s ease; z-index: 10;
    }
    .avatar-circle {
        background: white; border: 3px solid white; border-radius: 50%; 
        width: 45px; height: 45px; 
        display: flex; align-items: center; justify-content: center;
        font-size: 26px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    /* 3. 정보 그리드 (Info) - 하단 배치 */
    .grid-card {
        background: white; border-radius: 18px; padding: 20px 15px; text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03); height: 100%;
        display: flex; flex-direction: column; justify-content: center;
    }
    .grid-label { font-size: 12px; color: #8E8E93; font-weight: 700; margin-bottom: 5px; }
    .grid-value { font-size: 22px; color: #1C1C1E; font-weight: 800; letter-spacing: -0.5px; }
    .grid-sub { font-size: 11px; color: #AEAEB2; margin-top: 4px; font-weight: 500;}
    
    .txt-red { color: #FF453A !important; }
    .txt-blue { color: #007AFF !important; }
    .txt-green { color: #34C759 !important; }

    /* 모바일 여백 수정 */
    .block-container { padding-top: 1rem; padding-bottom: 5rem; }
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
# 🔧 Admin Console (V20 - 롤백됨 ㅆㅂ)
# --------------------------------------------------
with st.sidebar:
    st.header("🎬 Director Mode")
    
    st.subheader("1. 버스 상황")
    prev_bus_status = st.radio("출발 상태", ["🟢 빈 자리 남고 출발", "🔴 만석으로 출발"], index=0)
    admin_time_passed = st.slider("이전 버스 경과 (분)", 0, 60, 25)
    admin_seats = st.slider("잔여 좌석 (석)", 0, 45, 4)
    
    st.subheader("2. 날씨 & 기온")
    weather = st.radio("날씨", ["☀️", "🌧️", "❄️"], horizontal=True)
    
    st.subheader("3. 사용자 이동")
    journey_progress = st.slider("목적지까지 진행률 (%)", 0, 100, 0)
    
    st.subheader("4. 속도")
    admin_speed = st.slider("기초 속도 (km/h)", 2.0, 15.0, 5.0)

    st.subheader("5. 타겟")
    target_station = st.selectbox("목적지", list(station_db.keys()))
    target_bus = st.selectbox("버스", station_db[target_station]["buses"])

# --------------------------------------------------
# 🖥️ 메인 로직 & UI
# --------------------------------------------------

# 로직 계산
origin = USER_ORIGIN
dest = station_db[target_station]["coords"]
curr_pos = interpolate_pos(origin, dest, journey_progress / 100)
dist_km = calculate_distance(curr_pos[0], curr_pos[1], dest[0], dest[1])
req_time = 0 if dist_km < 0.02 else (dist_km / admin_speed) * 60

# 대기열 로직 (부등호 티배깅 뺌 ㅆㅂ)
base_queue = 0 if "빈 자리" in prev_bus_status else 25
q_future = base_queue + int(admin_time_passed * 0.5) + (0.5 * req_time)
bus_eta = 15

# 상태 결정
if journey_progress >= 100:
    theme, icon, title, sub = "hero-blue", "🏁", "도착 완료", "수고하셨습니다!"
elif req_time > bus_eta:
    theme, icon, title, sub = "hero-red", "🚫", "탑승 불가", f"버스 도착 {bus_eta}분 전"
elif q_future > admin_seats:
    theme, icon, title, sub = "hero-red", "😱", "포기해", f"예상 대기 {int(q_future)}명 (만석)"
elif q_future > (admin_seats - 5):
    theme, icon, title, sub = "hero-yellow", "🏃", "지금 뛰어!", f"막차 가능성 있음 ({int(admin_seats)}석)"
else:
    theme, icon, title, sub = "hero-green", "☕️", "여유 있음", "천천히 걸어가세요"


# [1] 헤더 (Header) - 흰 박스 없애고 깔끔하게
st.markdown(f"""
<div class="app-header">
    <div class="app-logo">TANA</div>
    <div class="weather-pill">{weather} 18°C</div>
</div>
""", unsafe_allow_html=True)


# [2] 액션 카드 (Hero) - 메인 강조
st.markdown(f"""
<div class="hero-card {theme}">
    <span class="hero-icon">{icon}</span>
    <h1 class="hero-title">{title}</h1>
    <div class="hero-sub">{sub}</div>
</div>
""", unsafe_allow_html=True)


# [3] 라이브 루트 (Visualization) - 중간 배치!
bar_color = "#34C759" if "green" in theme else ("#FF9F0A" if "yellow" in theme else "#FF453A")
if "blue" in theme: bar_color = "#007AFF"

st.markdown(f"""
<div class="route-container">
    <div class="route-header">
        <span>LIVE TRACKING</span>
        <span>{int(dist_km*1000)}M 남음</span>
    </div>
    <div style="position: relative; height: 50px;">
        <div class="track-bg">
            <div class="track-fill" style="width: {journey_progress}%; background: {bar_color};"></div>
        </div>
        <div class="avatar-wrapper" style="left: {journey_progress}%;">
            <div class="avatar-circle">
                {'🚀' if admin_speed > 10 else ('🏃' if admin_speed > 6 else '🚶')}
            </div>
        </div>
    </div>
    <div style="text-align:center; margin-top:10px; font-size:12px; color:#8E8E93;">
        현재 속도 <b>{admin_speed} km/h</b>로 이동 중
    </div>
</div>
""", unsafe_allow_html=True)


# [4] 정보 그리드 (Info) - 하단 배치, 부등호 뺌
c1, c2 = st.columns(2)
with c1:
    st.markdown(f"""
    <div class="grid-card">
        <div class="grid-label">👥 대기 인원</div>
        <div class="grid-value">{int(q_future)}명</div>
        <div class="grid-sub">현재 {int(base_queue + admin_time_passed*0.5)}명 대기 중</div>
    </div>
    <div style="height:15px"></div>
    <div class="grid-card">
        <div class="grid-label">⏱ 소요 시간</div>
        <div class="grid-value">{int(req_time)}분</div>
        <div class="grid-sub">도착 예정</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    seat_cls = "txt-red" if admin_seats < 5 else "txt-green"
    st.markdown(f"""
    <div class="grid-card">
        <div class="grid-label">💺 잔여 좌석</div>
        <div class="grid-value {seat_cls}">{admin_seats}석</div>
        <div class="grid-sub">버스 도착 {bus_eta}분 전</div>
    </div>
    <div style="height:15px"></div>
    <div class="grid-card">
        <div class="grid-label">🚌 버스 정보</div>
        <div class="grid-value txt-blue">{target_bus}</div>
        <div class="grid-sub">{target_station}행</div>
    </div>
    """, unsafe_allow_html=True)
