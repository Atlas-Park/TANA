import streamlit as st
import pandas as pd
import numpy as np
import math
import pydeck as pdk
import base64
import textwrap

# 페이지 설정
st.set_page_config(page_title="TANA", page_icon="🚦", layout="centered")

# --------------------------------------------------
# 🎨 CSS 스타일 (Fix: 겹침 해결 & 위계 수정)
# --------------------------------------------------
st.markdown("""
<style>
    @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.8/dist/web/static/pretendard.css");
    
    .main {
        background-color: #F2F2F7;
        font-family: 'Pretendard', sans-serif;
    }
    
    /* [New] 입력 섹션 (Input Card) */
    .input-card {
        background: white; border-radius: 20px; padding: 20px; margin-bottom: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.03);
    }
    .input-label { font-size: 12px; color: #8E8E93; font-weight: 700; margin-bottom: 8px; }

    /* 헤더 */
    .app-header {
        display: flex; justify-content: space-between; align-items: center;
        padding: 10px 5px 20px 5px;
    }
    .app-logo { font-size: 24px; font-weight: 900; letter-spacing: -1px; }
    .weather-pill { 
        background: white; padding: 6px 12px; border-radius: 30px; 
        font-size: 13px; font-weight: 600; color: #1C1C1E;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }

    /* 액션 카드 (Hero) - 애니메이션 유지 */
    .hero-card {
        border-radius: 24px; padding: 30px 20px; text-align: center; color: white; margin-bottom: 20px;
        animation: pulse 2s infinite ease-in-out;
        box-shadow: 0 10px 25px rgba(0,0,0,0.15);
    }
    /* 색상 테마 */
    .hero-green { background: linear-gradient(135deg, #34C759, #30B0C7); }
    .hero-yellow { background: linear-gradient(135deg, #FF9F0A, #FF375F); }
    .hero-red { background: linear-gradient(135deg, #FF453A, #FF375F); }
    .hero-blue { background: linear-gradient(135deg, #007AFF, #5AC8FA); }

    .hero-title { font-size: 32px; font-weight: 800; margin: 0; line-height: 1.1; }
    .hero-sub { font-size: 16px; font-weight: 500; margin-top: 8px; opacity: 0.95; }

    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.01); }
        100% { transform: scale(1); }
    }

    /* 데이터 그리드 (Info Grid) - 위계 상승 */
    .grid-card {
        background: white; border-radius: 18px; padding: 16px; text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03); height: 100%;
        display: flex; flex-direction: column; justify-content: center;
    }
    .grid-label { font-size: 11px; color: #8E8E93; font-weight: 600; margin-bottom: 4px; text-transform: uppercase; }
    .grid-value { font-size: 20px; color: #1C1C1E; font-weight: 800; letter-spacing: -0.5px; }
    .grid-sub { font-size: 10px; color: #AEAEB2; margin-top: 2px; }
    
    .txt-red { color: #FF453A !important; }
    .txt-blue { color: #007AFF !important; }
    .txt-green { color: #34C759 !important; }

    /* 라이브 루트 (Live Route) - 위계 하락 & 겹침 수정 */
    .route-container {
        background: white; border-radius: 20px; padding: 24px 20px; margin-top: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
    }
    .route-header { 
        font-size: 12px; color: #8E8E93; font-weight: 700; margin-bottom: 25px; /* 마진 확보 */
        display: flex; justify-content: space-between;
    }
    
    /* 진행 바 & 아바타 */
    .track-bg {
        width: 100%; height: 6px; background: #F2F2F7; border-radius: 3px; position: relative;
    }
    .track-fill {
        height: 100%; border-radius: 3px; transition: width 0.3s ease;
    }
    .avatar-wrapper {
        position: absolute; top: 50%; transform: translate(-50%, -50%); 
        transition: left 0.3s ease;
        z-index: 10;
    }
    .avatar-circle {
        background: white; border: 2px solid white; border-radius: 50%; 
        width: 36px; height: 36px; 
        display: flex; align-items: center; justify-content: center;
        font-size: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    
    /* 지도 배경 */
    .map-bg {
        margin-top: 15px; border-radius: 12px; overflow: hidden; opacity: 0.5; filter: grayscale(100%); height: 120px;
    }
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
# 🏗️ UI 구조 (Layout)
# --------------------------------------------------

# [1] 헤더 (Header)
st.markdown("""
<div class="app-header">
    <div class="app-logo">TANA</div>
    <div class="weather-pill">☀️ 18°C</div>
</div>
""", unsafe_allow_html=True)

# [2] 사용자 입력 (User Input) - 메인으로 이동!
st.markdown('<div class="input-card">', unsafe_allow_html=True)
c_in1, c_in2 = st.columns(2)
with c_in1:
    st.markdown('<div class="input-label">출발 정류장</div>', unsafe_allow_html=True)
    target_station = st.selectbox("정류장 선택", list(station_db.keys()), label_visibility="collapsed")
with c_in2:
    st.markdown('<div class="input-label">탑승 버스</div>', unsafe_allow_html=True)
    target_bus = st.selectbox("버스 선택", station_db[target_station]["buses"], label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)

# --- Admin Control (숨김/사이드바) ---
with st.sidebar:
    st.header("Admin Controls")
    journey_progress = st.slider("진행률", 0, 100, 0)
    admin_speed = st.slider("속도", 2.0, 15.0, 5.0)
    admin_time_passed = st.slider("버스 경과", 0, 60, 25)
    admin_seats = st.slider("잔여 좌석", 0, 45, 4)

# --- 로직 계산 ---
origin = USER_ORIGIN
dest = station_db[target_station]["coords"]
curr_pos = interpolate_pos(origin, dest, journey_progress / 100)
dist_km = calculate_distance(curr_pos[0], curr_pos[1], dest[0], dest[1])
req_time = 0 if dist_km < 0.02 else (dist_km / admin_speed) * 60
q_future = 25 + int(admin_time_passed * 0.5) + (0.5 * req_time) # 간소화 로직
bus_eta = 15

# 상태 결정
if journey_progress >= 100:
    theme, icon, title, sub = "hero-blue", "🏁", "도착 완료", "고생하셨습니다!"
elif req_time > bus_eta:
    theme, icon, title, sub = "hero-red", "🚫", "탑승 불가", f"버스 도착 {bus_eta}분 전"
elif q_future > admin_seats:
    theme, icon, title, sub = "hero-red", "😱", "포기해", f"대기 {int(q_future)}명 > 잔여 {admin_seats}석"
elif q_future > (admin_seats - 5):
    theme, icon, title, sub = "hero-yellow", "🏃", "지금 뛰어!", f"막차 가능성 있음 ({int(admin_seats)}석)"
else:
    theme, icon, title, sub = "hero-green", "☕️", "여유 있음", "천천히 걸어가세요"

# [3] 액션 카드 (Hero)
st.markdown(f"""
<div class="hero-card {theme}">
    <div style="font-size:40px; margin-bottom:10px;">{icon}</div>
    <h1 class="hero-title">{title}</h1>
    <div class="hero-sub">{sub}</div>
</div>
""", unsafe_allow_html=True)

# [4] 정보 그리드 (Info Grid) - 지도보다 위로 올림!
c1, c2 = st.columns(2)
with c1:
    st.markdown(f"""
    <div class="grid-card">
        <div class="grid-label">👥 예상 대기열</div>
        <div class="grid-value">{int(q_future)}명</div>
        <div class="grid-sub">현재 {int(25 + admin_time_passed*0.5)}명 + 유입</div>
    </div>
    <div style="height:10px"></div>
    <div class="grid-card">
        <div class="grid-label">⏱ 도착까지</div>
        <div class="grid-value">{int(req_time)}분 {int((req_time%1)*60)}초</div>
        <div class="grid-sub">속도 {admin_speed}km/h</div>
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
    <div style="height:10px"></div>
    <div class="grid-card">
        <div class="grid-label">🚌 버스 정보</div>
        <div class="grid-value txt-blue">{target_bus}</div>
        <div class="grid-sub">{target_station}행</div>
    </div>
    """, unsafe_allow_html=True)

# [5] 라이브 루트 (Live Route) - 맨 아래로 배치
bar_color = "#34C759" if "green" in theme else ("#FF9F0A" if "yellow" in theme else "#FF453A")
if "blue" in theme: bar_color = "#007AFF"

st.markdown(f"""
<div class="route-container">
    <div class="route-header">
        <span>LIVE ROUTE</span>
        <span>{int(dist_km*1000)}m 남음</span>
    </div>
    <div style="position: relative; height: 40px;">
        <div class="track-bg">
            <div class="track-fill" style="width: {journey_progress}%; background: {bar_color};"></div>
        </div>
        <div class="avatar-wrapper" style="left: {journey_progress}%;">
            <div class="avatar-circle">
                {'🚀' if admin_speed > 10 else ('🏃' if admin_speed > 6 else '🚶')}
            </div>
        </div>
    </div>
    <div class="map-bg">
""", unsafe_allow_html=True)

# 지도 렌더링
view_state = pdk.ViewState(latitude=curr_pos[0], longitude=curr_pos[1], zoom=14.5)
r = pdk.Deck(
    layers=[
        pdk.Layer("ScatterplotLayer", data=[{"pos": origin}, {"pos": dest}], get_position="pos", get_color=[100,100,100], get_radius=50),
        pdk.Layer("PathLayer", data=[{"path": [[origin[1], origin[0]], [dest[1], dest[0]]]}], get_path="path", get_color=[200,200,200], get_width=10)
    ],
    initial_view_state=view_state,
    map_style="mapbox://styles/mapbox/light-v9",
)
st.pydeck_chart(r, use_container_width=True)
st.markdown("</div></div>", unsafe_allow_html=True)
