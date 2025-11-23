import streamlit as st
import pandas as pd
import numpy as np
import math
import pydeck as pdk
import base64
import textwrap

# 페이지 설정
st.set_page_config(page_title="타나(TANA)", page_icon="🚦", layout="centered")

# --------------------------------------------------
# 🎨 CSS 스타일 (Legendary Edition)
# --------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700;900&display=swap');
    
    .main { background-color: #f8f9fa; font-family: 'Noto Sans KR', sans-serif; }
    
    /* 1. 통합 헤더 (프로필 + 날씨 + 광고) */
    .header-card {
        background: white;
        border-radius: 16px;
        padding: 12px 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
    }
    .header-left { display: flex; flex-direction: column; }
    .user-name { font-size: 18px; font-weight: 900; color: #212529; }
    .weather-info { font-size: 13px; color: #868e96; display: flex; align-items: center; gap: 5px; }
    .ad-pill {
        background: linear-gradient(135deg, #6610f2, #20c997);
        color: white; font-size: 11px; font-weight: bold;
        padding: 4px 10px; border-radius: 20px;
        text-decoration: none;
        box-shadow: 0 2px 5px rgba(102, 16, 242, 0.3);
        animation: pulse 2s infinite;
    }

    /* 2. 공항형 도착 보드 (Arrival Board) */
    .arrival-board {
        background-color: #212529;
        color: #f8f9fa;
        border-radius: 12px;
        padding: 15px 20px;
        margin-bottom: 15px;
        box-shadow: 0 8px 15px rgba(0,0,0,0.2);
        border-left: 5px solid #20c997; /* TANA Mint */
    }
    .board-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; }
    .bus-num { font-size: 24px; font-weight: 900; color: #fff; letter-spacing: 1px; }
    .bus-status { font-size: 14px; color: #20c997; font-weight: bold; text-transform: uppercase; }
    .board-detail { font-size: 13px; color: #adb5bd; display: flex; gap: 15px; font-family: monospace; }

    /* 3. 아바타 애니메이션 (CSS Magic) */
    @keyframes float { 0% { transform: translateY(0px); } 50% { transform: translateY(-5px); } 100% { transform: translateY(0px); } }
    @keyframes run { 0% { transform: skewX(0deg) translateX(0); } 25% { transform: skewX(-5deg) translateX(2px); } 75% { transform: skewX(5deg) translateX(-2px); } 100% { transform: skewX(0deg) translateX(0); } }
    @keyframes shake { 0% { transform: translate(1px, 1px) rotate(0deg); } 10% { transform: translate(-1px, -2px) rotate(-1deg); } 20% { transform: translate(-3px, 0px) rotate(1deg); } 30% { transform: translate(3px, 2px) rotate(0deg); } 40% { transform: translate(1px, -1px) rotate(1deg); } 50% { transform: translate(-1px, 2px) rotate(-1deg); } 60% { transform: translate(-3px, 1px) rotate(0deg); } 70% { transform: translate(3px, 1px) rotate(-1deg); } 80% { transform: translate(-1px, -1px) rotate(1deg); } 90% { transform: translate(1px, 2px) rotate(0deg); } 100% { transform: translate(1px, -2px) rotate(-1deg); } }
    @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.05); } 100% { transform: scale(1); } }

    .avatar-box { height: 100px; display: flex; justify-content: center; align-items: center; margin: 10px 0; }
    .avatar-img { height: 90px; width: auto; filter: drop-shadow(0 8px 10px rgba(0,0,0,0.15)); }
    
    /* 상태별 애니메이션 클래스 */
    .anim-walk { animation: float 1.5s ease-in-out infinite; }
    .anim-run { animation: run 0.3s linear infinite; }
    .anim-rocket { animation: shake 0.5s linear infinite; }

    /* 4. 3분할 결과 카드 (The Result) */
    .result-card {
        background: white;
        border-radius: 24px;
        padding: 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08);
        overflow: hidden;
        text-align: center;
        margin-top: 20px;
    }
    
    /* 상단: 인디케이터 영역 */
    .result-header { padding: 25px 20px 10px; }
    .status-circle {
        width: 60px; height: 60px; border-radius: 50%; margin: 0 auto 10px;
        display: flex; align-items: center; justify-content: center;
        font-size: 30px; box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    
    /* 중단: 행동 지침 */
    .result-action { padding: 0 20px 15px; }
    .action-title { font-size: 22px; font-weight: 900; color: #212529; margin-bottom: 5px; }
    .action-desc { font-size: 15px; color: #495057; line-height: 1.4; }

    /* 하단: 데이터 그리드 */
    .result-data {
        background-color: #f8f9fa;
        border-top: 1px solid #eee;
        padding: 15px;
        display: flex; justify-content: space-around;
    }
    .data-item { display: flex; flex-direction: column; }
    .data-label { font-size: 11px; color: #868e96; font-weight: 600; text-transform: uppercase; }
    .data-value { font-size: 16px; color: #212529; font-weight: 800; }

    /* 색상 테마 */
    .theme-green .status-circle { background: #d3f9d8; color: #2b8a3e; }
    .theme-green .action-title { color: #2b8a3e; }
    
    .theme-yellow .status-circle { background: #fff3bf; color: #f08c00; }
    .theme-yellow .action-title { color: #f08c00; }
    
    .theme-red .status-circle { background: #ffe3e3; color: #c92a2a; }
    .theme-red .action-title { color: #c92a2a; }
    
    .theme-blue .status-circle { background: #e7f5ff; color: #1864ab; }
    .theme-blue .action-title { color: #1864ab; }

</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# 🛠️ 기능 함수
# --------------------------------------------------
def get_img_as_base64(file_path):
    try:
        with open(file_path, "rb") as f: return base64.b64encode(f.read()).decode()
    except: return None

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

# [New] 내러티브 생성기 (숫자 -> 문장)
def generate_narrative(status, time, queue, seats):
    if status == "green":
        return f"현재 속도라면 <b>{format_time(time)}</b> 뒤에 도착해요. <br>이어폰 끼고 천천히 걸어가도 충분합니다 🎵"
    elif status == "yellow":
        return f"지금 바로 뛰면 <b>{int(queue)}번째</b>로 줄을 설 수 있어요.<br>막차 탑승 확률 <b>85%</b>입니다! 🏃💨"
    elif status == "red":
        if queue > seats + 20:
            return f"줄이 너무 깁니다 (예상 <b>{int(queue)}명</b>).<br>깔끔하게 포기하고 다음 차나 지하철을 추천해요."
        else:
            return f"버스가 <b>{format_time(time)}</b> 안에 떠납니다.<br>물리적으로 도착이 불가능해요 💦"
    else:
        return "목적지에 도착했습니다! 오늘도 수고하셨어요 🏁"

# --------------------------------------------------
# 📍 데이터
# --------------------------------------------------
USER_ORIGIN = [37.3835, 126.6550]
station_db = {
    "연세대학교 (국제)": {"coords": [37.3815, 126.6580], "buses": ["M6724", "9201"]},
    "박문여자고등학교": {"coords": [37.3948, 126.6672], "buses": ["순환41", "9"]},
    "박문중학교": {"coords": [37.3932, 126.6682], "buses": ["순환41"]}
}

# --------------------------------------------------
# 🔧 Admin Console (V18)
# --------------------------------------------------
with st.sidebar:
    st.header("🎬 TANA V18 Legend")
    st.subheader("1. 버스 상황")
    prev_bus_status = st.radio("출발 상태", ["🟢 빈 자리 남고 출발 (리셋 O)", "🔴 만석으로 출발 (리셋 X)"], index=0)
    admin_time_passed = st.slider("이전 버스 경과 (분)", 0, 60, 25)
    admin_seats = st.slider("잔여 좌석 (석)", 0, 45, 15)
    
    st.subheader("2. 날씨")
    current_weather = st.radio("날씨", ["맑음 ☀️", "흐림 ☁️", "비 🌧️", "눈 ❄️"], horizontal=True)
    admin_temp = st.slider("기온", -15, 40, 18)
    
    st.subheader("3. 사용자 이동")
    journey_progress = st.slider("진행률 (%)", 0, 100, 0)
    admin_speed = st.slider("기초 속도", 2.0, 15.0, 5.0, step=0.1)

# --------------------------------------------------
# 📱 메인 UI
# --------------------------------------------------

# 1. 통합 헤더 (Profile + Weather + Ad)
st.markdown(f"""
    <div class="header-card">
        <div class="header-left">
            <div class="user-name">박연세 님 👋</div>
            <div class="weather-info">
                <span>{current_weather}</span>
                <span>•</span>
                <span>{admin_temp}℃</span>
                <span>•</span>
                <span>체감 {admin_temp-2}℃</span>
            </div>
        </div>
        <a href="#" class="ad-pill">🎁 메가커피 쿠폰받기</a>
    </div>
""", unsafe_allow_html=True)

# 2. 미니맵 (상단 고정)
# 좌표 및 버스 선택 로직
c1, c2 = st.columns([1.3, 1])
with c1: target_station_name = st.selectbox("탑승 정류장", list(station_db.keys()), label_visibility="collapsed")
with c2: target_bus = st.selectbox("버스", station_db[target_station_name]["buses"], label_visibility="collapsed")

origin_coords = USER_ORIGIN
dest_coords = station_db[target_station_name]["coords"]
current_user_coords = interpolate_pos(origin_coords, dest_coords, journey_progress / 100)

# 지도 세션 관리
if 'view_state' not in st.session_state:
    st.session_state.view_state = pdk.ViewState(latitude=(origin_coords[0]+dest_coords[0])/2, longitude=(origin_coords[1]+dest_coords[1])/2, zoom=15)
if st.button("📍 현위치로 지도 이동"):
    st.session_state.view_state = pdk.ViewState(latitude=current_user_coords[0], longitude=current_user_coords[1], zoom=15)
elif journey_progress > 0: 
    st.session_state.view_state = pdk.ViewState(latitude=current_user_coords[0], longitude=current_user_coords[1], zoom=16)

# 지도 렌더링
path_data = pd.DataFrame([{'path': [ [origin_coords[1], origin_coords[0]], [dest_coords[1], dest_coords[0]] ]}])
point_data = pd.DataFrame([
    {'lat': origin_coords[0], 'lon': origin_coords[1], 'type': 'Start', 'color': [200,200,200,150], 'radius': 10},
    {'lat': dest_coords[0], 'lon': dest_coords[1], 'type': 'End', 'color': [32, 201, 151, 200], 'radius': 20}, # Mint Color
    {'lat': current_user_coords[0], 'lon': current_user_coords[1], 'type': 'User', 'color': [0,120,255,255], 'radius': 30}
])

r = pdk.Deck(
    layers=[
        pdk.Layer("PathLayer", path_data, get_path="path", width_scale=20, width_min_pixels=3, get_color=[180,180,180,100]),
        pdk.Layer("ScatterplotLayer", point_data, get_position='[lon, lat]', get_color='color', get_radius='radius')
    ],
    initial_view_state=st.session_state.view_state,
    map_style="mapbox://styles/mapbox/light-v9" 
)
st.pydeck_chart(r)

# 3. 계산 로직 (Logic Engine)
if current_weather == "맑음 ☀️": resist = 1.0
elif current_weather == "흐림 ☁️": resist = 0.95
elif current_weather == "비 🌧️": resist = 0.85
else: resist = 0.70 # 눈

effective_speed = admin_speed * resist
remain_distance = calculate_distance(current_user_coords[0], current_user_coords[1], dest_coords[0], dest_coords[1])
required_time = 0 if remain_distance < 0.02 else (remain_distance / effective_speed) * 60

# 대기열 계산
inflow_rate = 3.0 
base_queue = 0 if "빈 자리" in prev_bus_status else 25
current_queue = base_queue + int(admin_time_passed * inflow_rate)
future_queue = current_queue + (inflow_rate * required_time)
final_bus_time_for_calc = 15 

# 상태 판단
if journey_progress >= 100:
    theme = "theme-blue"
    icon = "🏁"
    title = "도착 완료"
elif required_time > final_bus_time_for_calc:
    theme = "theme-red"
    icon = "🚫"
    title = "탑승 불가"
elif future_queue > admin_seats: 
    theme = "theme-red"
    icon = "😱"
    title = "탑승 불가"
elif future_queue > (admin_seats - 5): 
    theme = "theme-yellow"
    icon = "🏃"
    title = "전력 질주!"
else:
    theme = "theme-green"
    icon = "☕"
    title = "여유 있음"

# 내러티브 생성
narrative_text = generate_narrative(theme.split("-")[1], required_time, future_queue, admin_seats)

# 4. 공항형 버스 보드 (Arrival Board)
if "빈 자리" in prev_bus_status:
    bus_status_msg = "ON TIME (RESET)"
else:
    bus_status_msg = f"DELAYED ({admin_time_passed} min)"

st.markdown(f"""
    <div class="arrival-board">
        <div class="board-row">
            <div class="bus-num">{target_bus}</div>
            <div class="bus-status">{bus_status_msg}</div>
        </div>
        <div class="board-row" style="margin-top:10px; padding-top:10px; border-top:1px dashed #495057;">
            <div class="board-detail">
                <span>ARRIVE: {final_bus_time_for_calc} MIN</span>
                <span>SEAT: {admin_seats}</span>
            </div>
            <div class="board-detail">
                <span>QUEUE: {int(future_queue)}</span>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# 5. 아바타 (CSS Animation 적용)
if effective_speed < 4.0: 
    img_file, anim_class = "img_slow.png", "anim-walk"
elif effective_speed < 8.0: 
    img_file, anim_class = "img_walk.png", "anim-walk"
elif effective_speed < 11.0: 
    img_file, anim_class = "img_run.png", "anim-run"
else: 
    img_file, anim_class = "img_rocket.png", "anim-rocket"

img_base64 = get_img_as_base64(img_file)
if img_base64:
    st.markdown(f"""
        <div class="avatar-box">
            <img src="data:image/png;base64,{img_base64}" class="avatar-img {anim_class}">
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"<div style='text-align:center; font-size:50px;'>🏃</div>", unsafe_allow_html=True)

# 6. 3단 합체 결과 카드 (Final UI)
st.markdown(f"""
    <div class="result-card {theme}">
        <div class="result-header">
            <div class="status-circle">{icon}</div>
        </div>
        <div class="result-action">
            <div class="action-title">{title}</div>
            <div class="action-desc">{narrative_text}</div>
        </div>
        <div class="result-data">
            <div class="data-item">
                <span class="data-label">남은 거리</span>
                <span class="data-value">{int(remain_distance*1000)}m</span>
            </div>
            <div class="data-item">
                <span class="data-label">현재 속도</span>
                <span class="data-value">{effective_speed:.1f} km/h</span>
            </div>
            <div class="data-item">
                <span class="data-label">도착 예상</span>
                <span class="data-value">{format_time(required_time)}</span>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)
