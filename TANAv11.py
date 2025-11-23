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
# 🎨 CSS 스타일 (Apple Wallet Style + Detail Fix)
# --------------------------------------------------
st.markdown("""
<style>
    @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.8/dist/web/static/pretendard.css");
    
    .main {
        background-color: #F2F2F7;
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
    }
    
    /* 상단 헤더 */
    .top-bar {
        display: flex; justify-content: space-between; align-items: center;
        margin-bottom: 15px; padding: 0 5px;
    }
    .app-title { font-size: 20px; font-weight: 900; color: #000; letter-spacing: -0.5px; }
    .status-pill { 
        font-size: 13px; font-weight: 600; color: #8E8E93; 
        background: rgba(255,255,255,0.8); padding: 6px 12px; border-radius: 20px;
        backdrop-filter: blur(10px);
    }

    /* 액션 카드 (Hero) */
    .hero-card {
        border-radius: 28px;
        padding: 30px 20px;
        text-align: center;
        color: white;
        margin-bottom: 25px;
        position: relative;
        overflow: hidden;
        animation: pulse 2s infinite ease-in-out;
        box-shadow: 0 15px 35px rgba(0,0,0,0.15); /* 그림자 강화 */
    }
    
    .hero-green { background: linear-gradient(135deg, #34C759 0%, #30B0C7 100%); }
    .hero-yellow { background: linear-gradient(135deg, #FF9F0A 0%, #FF375F 100%); }
    .hero-red { background: linear-gradient(135deg, #FF453A 0%, #FF375F 100%); }
    .hero-blue { background: linear-gradient(135deg, #007AFF 0%, #5AC8FA 100%); }

    .hero-icon { font-size: 48px; margin-bottom: 10px; display: block; }
    .hero-title { font-size: 28px; font-weight: 800; margin: 0; letter-spacing: -0.5px; line-height: 1.2; }
    .hero-sub { font-size: 15px; font-weight: 500; margin-top: 8px; opacity: 0.95; }

    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.01); }
        100% { transform: scale(1); }
    }

    /* 라이브 루트 (진행 바) */
    .route-container {
        background: white; border-radius: 24px; padding: 25px 20px; margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.03);
        /* [Fix] 아바타 잘림 방지 패딩 추가 */
        padding-left: 25px; padding-right: 25px; 
    }
    .route-header { font-size: 13px; color: #8E8E93; font-weight: 700; margin-bottom: 25px; text-transform: uppercase; letter-spacing: 1px;}
    
    .progress-track {
        width: 100%; height: 8px; background: #E5E5EA; border-radius: 4px; position: relative;
    }
    .progress-fill {
        height: 100%; border-radius: 4px; transition: width 0.5s ease;
    }
    .avatar-on-track {
        position: absolute; top: -38px; 
        transform: translateX(-50%); 
        transition: left 0.5s ease;
        font-size: 32px;
        z-index: 10;
    }

    /* 데이터 그리드 */
    .grid-card {
        background: white; border-radius: 20px; padding: 18px; text-align: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.02); height: 100%;
        display: flex; flex-direction: column; justify-content: center;
    }
    .grid-label { font-size: 12px; color: #8E8E93; font-weight: 600; margin-bottom: 4px; }
    .grid-value { font-size: 22px; color: #1C1C1E; font-weight: 800; letter-spacing: -0.5px; }
    .grid-sub { font-size: 11px; color: #AEAEB2; margin-top: 4px; }
    
    .text-red { color: #FF453A; }
    .text-blue { color: #007AFF; }
    .text-green { color: #34C759; }

    /* 지도 흑백 처리 & 높이 고정 */
    .map-wrapper {
        filter: grayscale(100%) opacity(0.5);
        border-radius: 16px;
        overflow: hidden;
        margin-top: 10px;
        border: 1px solid #E5E5EA;
        height: 180px; /* [Fix] 높이 강제 고정 (콤팩트하게) */
    }
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# 🛠️ 기능 함수
# --------------------------------------------------
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

def format_time(minutes):
    mins = int(minutes)
    secs = int((minutes - mins) * 60)
    if mins == 0: return f"{secs}초"
    return f"{mins}분 {secs}초"

# --------------------------------------------------
# 📍 데이터
# --------------------------------------------------
USER_ORIGIN = [37.3835, 126.6550] 
station_db = {
    "연세대학교": {"coords": [37.3815, 126.6580], "buses": ["M6724", "9201"]},
    "박문여고": {"coords": [37.3948, 126.6672], "buses": ["순환41", "9"]},
    "박문중": {"coords": [37.3932, 126.6682], "buses": ["순환41"]}
}

# --------------------------------------------------
# 🔧 Admin Console (감독판)
# --------------------------------------------------
with st.sidebar:
    st.header("🎬 TANA V21.1 Final")
    
    journey_progress = st.slider("🏃 이동 진행률 (%)", 0, 100, 0)
    admin_speed = st.slider("⚡ 현재 속도 (km/h)", 2.0, 15.0, 5.0)
    st.divider()
    admin_time_passed = st.slider("버스 경과 (분)", 0, 60, 25)
    admin_seats = st.slider("잔여 좌석", 0, 45, 8) 
    st.divider()
    target_station = st.selectbox("목적지", list(station_db.keys()))
    target_bus = st.selectbox("버스", station_db[target_station]["buses"])
    is_reset = st.toggle("리셋 포인트", False)
    weather = st.radio("날씨", ["☀️", "🌧️", "❄️"], horizontal=True)

# --------------------------------------------------
# 📱 로직 계산
# --------------------------------------------------
origin = USER_ORIGIN
dest = station_db[target_station]["coords"]
curr_pos = interpolate_pos(origin, dest, journey_progress / 100)
dist = calculate_distance(curr_pos[0], curr_pos[1], dest[0], dest[1])

resist = 1.0 if weather == "☀️" else (0.85 if weather == "🌧️" else 0.7)
real_speed = admin_speed * resist
req_time = 0 if dist < 0.02 else (dist / real_speed) * 60

q_base = 0 if is_reset else 25
q_curr = q_base + int(admin_time_passed * 3.0)
q_future = q_curr + (3.0 * req_time)
bus_eta = 15 

# 상태 판단
if journey_progress >= 100:
    theme = "hero-blue"
    icon = "🏁"
    title = "도착 완료!"
    sub = "수고하셨습니다 :)"
elif req_time > bus_eta:
    theme = "hero-red"
    icon = "🚫"
    title = "탑승 불가"
    sub = f"도착 전 버스 떠남 ({bus_eta}분 후)"
elif q_future > admin_seats:
    theme = "hero-red"
    icon = "😱"
    title = "지금은 포기해"
    sub = f"줄이 너무 깁니다 (예상 {int(q_future)}명)"
elif q_future > (admin_seats - 5):
    theme = "hero-yellow"
    icon = "🏃💨"
    title = "지금 뛰어!!"
    sub = f"전력 질주 시 막차 가능 (잔여 {admin_seats}석)"
else:
    theme = "hero-green"
    icon = "☕️"
    title = "천천히 가요"
    sub = f"여유 있습니다 (예상 대기 {int(q_future)}명)"

# --------------------------------------------------
# 🖥️ UI 렌더링
# --------------------------------------------------

# [1] 최상단 헤더
c1, c2 = st.columns([1, 1])
with c1: st.markdown('<div class="app-title">TANA</div>', unsafe_allow_html=True)
with c2: st.markdown(f'<div style="text-align:right;"><span class="status-pill">{weather} 18°C</span></div>', unsafe_allow_html=True)

# [2] 액션 카드 (Hero)
st.markdown(textwrap.dedent(f"""
    <div class="hero-card {theme}">
        <span class="hero-icon">{icon}</span>
        <h1 class="hero-title">{title}</h1>
        <div class="hero-sub">{sub}</div>
    </div>
"""), unsafe_allow_html=True)

# [3] 라이브 루트 (Visualization)
bar_color = "#34C759" if "green" in theme else ("#FF9F0A" if "yellow" in theme else "#FF453A")
if "blue" in theme: bar_color = "#007AFF"

st.markdown(textwrap.dedent(f"""
    <div class="route-container">
        <div class="route-header">LIVE TRACKING • {target_bus}</div>
        <div style="position: relative; height: 40px; display: flex; align-items: center;">
            <div class="progress-track">
                <div class="progress-fill" style="width: {journey_progress}%; background-color: {bar_color};"></div>
            </div>
            <div class="avatar-on-track" style="left: {journey_progress}%;">
                <div style="background:white; border-radius:50%; padding:2px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
                    {'🚀' if real_speed > 10 else ('🏃' if real_speed > 6 else '🚶')}
                </div>
            </div>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:12px; color:#8E8E93; margin-top:5px;">
            <span>출발</span>
            <span><b>{int(dist*1000)}m</b> 남음</span>
            <span>도착</span>
        </div>
    </div>
"""), unsafe_allow_html=True)

# [3-1] 지도 (배경용, 높이 고정 Fix)
view_state = pdk.ViewState(latitude=curr_pos[0], longitude=curr_pos[1], zoom=15)
r = pdk.Deck(
    layers=[
        pdk.Layer("ScatterplotLayer", data=[{"pos": origin}, {"pos": dest}], get_position="pos", get_color=[200,200,200], get_radius=30),
        pdk.Layer("PathLayer", data=[{"path": [[origin[1], origin[0]], [dest[1], dest[0]]]}], get_path="path", get_color=[200,200,200], get_width=5)
    ],
    initial_view_state=view_state,
    map_style="mapbox://styles/mapbox/light-v9",
    height=180 # [Fix] 높이 강제 고정
)
# CSS 클래스로 한 번 더 감싸기 (스타일 적용)
st.markdown('<div class="map-wrapper">', unsafe_allow_html=True)
st.pydeck_chart(r, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)


# [4] 데이터 그리드
c1, c2 = st.columns(2)
with c1:
    st.markdown(f"""
        <div class="grid-card">
            <div class="grid-label">👥 예상 대기</div>
            <div class="grid-value">{int(q_future)}명</div>
            <div class="grid-sub">현재 {int(q_curr)}명 + 유입</div>
        </div>
        <div style="height:10px;"></div>
        <div class="grid-card">
            <div class="grid-label">⏱ 도착 예정</div>
            <div class="grid-value">{format_time(req_time)}</div>
            <div class="grid-sub">현재 속도 {real_speed:.1f}km/h</div>
        </div>
    """, unsafe_allow_html=True)

with c2:
    seat_color = "text-red" if admin_seats < 5 else "text-green"
    st.markdown(f"""
        <div class="grid-card">
            <div class="grid-label">💺 잔여 좌석</div>
            <div class="grid-value {seat_color}">{admin_seats}석</div>
            <div class="grid-sub">버스 도착 {bus_eta}분 전</div>
        </div>
        <div style="height:10px;"></div>
        <div class="grid-card">
            <div class="grid-label">🚌 탑승 버스</div>
            <div class="grid-value text-blue">{target_bus}</div>
            <div class="grid-sub">목적지: {target_station}</div>
        </div>
    """, unsafe_allow_html=True)
