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
# 🎨 CSS 스타일
# --------------------------------------------------
st.markdown("""
<style>
    .main { background-color: #ffffff; }
    
    /* 광고 배너 */
    .ad-box {
        background-color: #f8f9fa; border: 1px dashed #ced4da; border-radius: 8px;
        padding: 12px; text-align: center; margin-bottom: 20px; color: #868e96; font-size: 13px;
        display: flex; align-items: center; justify-content: center;
    }
    .ad-badge {
        background-color: #adb5bd; color: white; font-size: 10px; padding: 2px 6px; 
        border-radius: 4px; margin-right: 8px; font-weight: bold;
    }

    /* 프로필 & 날씨 */
    .profile-container {
        display: flex; justify-content: space-between; align-items: center;
        padding: 5px 10px; margin-bottom: 10px;
    }
    .profile-left { display: flex; align-items: center; }
    .profile-img { 
        width: 40px; height: 40px; border-radius: 50%; background-color: #e9ecef; 
        display: flex; align-items: center; justify-content: center; font-size: 22px; margin-right: 10px; 
    }
    .profile-name { font-size: 16px; font-weight: 800; color: #2c3e50; }
    .weather-badge {
        font-size: 14px; font-weight: 600; color: #495057; background-color: #fff;
        padding: 6px 14px; border-radius: 20px; border: 1px solid #dee2e6; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.03); display: flex; gap: 8px; align-items: center;
    }

    /* UI 박스 공통 */
    .search-container { 
        background-color: #fff; border: 1px solid #e0e0e0; border-radius: 15px; 
        padding: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.02); margin-bottom: 10px; 
    }
    .info-text-box { 
        font-size: 16px; color: #495057; background-color: #f1f3f5; 
        padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 20px; border: 1px solid #dee2e6; font-weight: 600;
    }
    
    /* 게이지 바 */
    .gauge-label {
        display: flex; justify-content: space-between; font-size: 13px; font-weight: 700; color: #343a40; margin-bottom: 5px;
    }
    .gauge-bg {
        width: 100%; height: 12px; background-color: #e9ecef; border-radius: 6px; position: relative; overflow: hidden; margin-bottom: 15px;
    }
    .gauge-fill {
        height: 100%; border-radius: 6px; transition: width 0.5s ease, background-color 0.5s ease;
    }
    
    /* 신호등 결과 박스 */
    .status-box { padding: 30px 20px; border-radius: 20px; text-align: center; color: white; margin-top: 20px; transition: all 0.3s ease; }
    .success-bg { background: linear-gradient(135deg, #28a745 0%, #20c997 100%); box-shadow: 0 10px 25px rgba(40, 167, 69, 0.3); }
    .warning-bg { background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%); color: #fff !important; text-shadow: 0 1px 2px rgba(0,0,0,0.1); box-shadow: 0 10px 25px rgba(255, 193, 7, 0.3); }
    .danger-bg { background: linear-gradient(135deg, #dc3545 0%, #c92a2a 100%); box-shadow: 0 10px 25px rgba(220, 53, 69, 0.3); }
    .arrival-bg { background: linear-gradient(135deg, #007bff 0%, #0062cc 100%); box-shadow: 0 10px 25px rgba(0, 123, 255, 0.3); }

    /* 결과창 내부 디테일 */
    .status-detail-container {
        display: flex; justify-content: space-around; align-items: center; margin-top: 25px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.3);
    }
    .detail-item-box { flex: 1; text-align: center; }
    .detail-divider { width: 1px; height: 30px; background-color: rgba(255,255,255,0.3); }
    .d-label { display: block; font-size: 12px; opacity: 0.9; margin-bottom: 4px; }
    .d-val { display: block; font-size: 18px; font-weight: 800; }

    /* 하단 요약 정보 */
    .summary-row { display: flex; justify-content: space-around; margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.3); font-size: 15px; }

    /* 아바타 */
    .avatar-container { text-align: center; margin-bottom: 5px; height: 80px; display: flex; align-items: center; justify-content: center; }
    .avatar-img { height: 80px; width: auto; object-fit: contain; filter: drop-shadow(0 5px 10px rgba(0,0,0,0.1)); } 
    .avatar-text { font-size: 60px; line-height: 1.0; }
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

def get_weather_factor(weather_condition):
    if weather_condition == "맑음 ☀️": return 1.0
    elif weather_condition == "흐림 ☁️": return 0.95
    elif weather_condition == "비 🌧️": return 0.85
    elif weather_condition == "눈 ❄️": return 0.70
    return 1.0

def format_time(minutes):
    mins = int(minutes)
    secs = int((minutes - mins) * 60)
    if mins == 0: return f"{secs}초"
    return f"{mins}분 {secs}초"

# --------------------------------------------------
# 📍 데이터
# --------------------------------------------------
default_start_locs = {
    "송도 2기숙사 (D동)": [37.3835, 126.6550],
    "송도 1기숙사 (A동)": [37.3820, 126.6570],
    "언더우드 기념도서관": [37.3805, 126.6590]
}
station_db = {
    "연세대학교 (국제)": {
        "coords": [37.3815, 126.6580],
        "buses": ["M6724", "9201"]
    },
    "박문여자고등학교": {
        "coords": [37.3948, 126.6672],
        "buses": ["순환41", "9"]
    },
    "박문중학교": {
        "coords": [37.3932, 126.6682],
        "buses": ["순환41"]
    }
}

# --------------------------------------------------
# 🔧 Admin Console (V16: 리셋 포인트 로직 강화)
# --------------------------------------------------
with st.sidebar:
    st.header("🎬 TANA Studio V16")
    
    st.subheader("1. 버스 상황")
    
    # [핵심 수정] 리셋 포인트 로직을 명확하게 분리
    prev_bus_status = st.radio(
        "이전 버스 출발 상태", 
        ["🟢 빈 자리 남고 출발 (리셋 O)", "🔴 만석으로 출발 (리셋 X)"],
        index=0
    )
    
    admin_time_passed = st.slider("이전 버스 경과 (분)", 0, 60, 25)
    admin_seats = st.slider("현재 버스 잔여 좌석 (석)", 0, 45, 15)
    
    st.subheader("2. 날씨 & 기온")
    current_weather = st.radio("날씨", ["맑음 ☀️", "흐림 ☁️", "비 🌧️", "눈 ❄️"], horizontal=True)
    admin_temp = st.slider("기온 (℃)", -15, 40, 18)
    
    st.subheader("3. 사용자 이동")
    journey_progress = st.slider("목적지까지 진행률 (%)", 0, 100, 0)
    
    st.subheader("4. 기초 능력치")
    admin_speed = st.slider("기초 속도 (km/h)", 2.0, 15.0, 5.0, step=0.1)


# --------------------------------------------------
# 📱 메인 화면 UI
# --------------------------------------------------

# 1. 타이틀 & 광고
st.title("타나(TANA)")
st.markdown(textwrap.dedent("""
    <div class="ad-box">
        <span class="ad-badge">AD</span>
        <span>기다리는 시간, <b>스타벅스</b>에서 따뜻하게 보내세요 (쿠폰받기)</span>
    </div>
"""), unsafe_allow_html=True)

# 2. 프로필 & 날씨
st.markdown(f"""
    <div class="profile-container">
        <div class="profile-left">
            <div class="profile-img">👤</div>
            <div class="profile-name">박연세 님</div>
        </div>
        <div class="weather-badge">
            <span>{current_weather}</span>
            <span style="color:#ced4da;">|</span>
            <span>{admin_temp}℃</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# 3. 탑승 정류장 & 버스 선택
st.markdown('<div class="search-container">', unsafe_allow_html=True)
c1, c2 = st.columns([1.3, 1])

with c1: 
    target_station_name = st.selectbox("탑승 정류장 (Destination)", list(station_db.keys()))

with c2: 
    available_buses = station_db[target_station_name]["buses"]
    target_bus = st.selectbox("탑승 버스", available_buses)

st.markdown('</div>', unsafe_allow_html=True)

# 좌표 설정
origin_coords = USER_ORIGIN
dest_coords = station_db[target_station_name]["coords"]
current_user_coords = interpolate_pos(origin_coords, dest_coords, journey_progress / 100)


# 4. [중요] 리셋 포인트 로직 및 상태 메시지
# 리셋 여부에 따라 '기본 대기열(backlog)'이 달라짐
is_reset = "빈 자리" in prev_bus_status

if is_reset:
    # 리셋 포인트: 대기열 0명에서 시작 + 시간 경과
    base_queue = 0
    status_badge = "✨ 리셋 포인트 (Reset Point)"
else:
    # 리셋 아님: 이월 인원(25명 가정) + 시간 경과
    base_queue = 25
    status_badge = "⚠️ 이월 인원 누적 (Backlog)"

status_text = f"📡 이전 {target_bus} 버스가 떠난 지 <b>{admin_time_passed}분</b> 지났습니다.<br><span style='font-size:12px; color:#888'>{status_badge}</span>"
st.markdown(f'<div class="info-text-box">{status_text}</div>', unsafe_allow_html=True)


# 5. 지도 시각화 (Session State 유지)
if 'view_state' not in st.session_state:
    st.session_state.view_state = pdk.ViewState(latitude=(origin_coords[0]+dest_coords[0])/2, longitude=(origin_coords[1]+dest_coords[1])/2, zoom=15)

if st.button("📍 현위치로 지도 이동"):
    st.session_state.view_state = pdk.ViewState(latitude=current_user_coords[0], longitude=current_user_coords[1], zoom=15)
elif journey_progress > 0: 
    st.session_state.view_state = pdk.ViewState(latitude=current_user_coords[0], longitude=current_user_coords[1], zoom=16)

path_data = pd.DataFrame([{'path': [ [origin_coords[1], origin_coords[0]], [dest_coords[1], dest_coords[0]] ]}])
point_data = pd.DataFrame([
    {'lat': origin_coords[0], 'lon': origin_coords[1], 'type': '출발', 'color': [200,200,200,150], 'radius': 10},
    {'lat': dest_coords[0], 'lon': dest_coords[1], 'type': '정류장', 'color': [255,50,50,200], 'radius': 20},
    {'lat': current_user_coords[0], 'lon': current_user_coords[1], 'type': '나', 'color': [0,120,255,255], 'radius': 30}
])

with st.expander("🗺️ 실시간 경로 추적 (View Map)", expanded=True):
    r = pdk.Deck(
        layers=[
            pdk.Layer("PathLayer", path_data, get_path="path", width_scale=20, width_min_pixels=3, get_color=[180,180,180,100]),
            pdk.Layer("ScatterplotLayer", point_data, get_position='[lon, lat]', get_color='color', get_radius='radius')
        ],
        initial_view_state=st.session_state.view_state
    )
    st.pydeck_chart(r)


# 6. 속도 & 진행률
resist_factor = get_weather_factor(current_weather)
effective_speed = admin_speed * resist_factor

if effective_speed < 4.0: img_file, emoji_backup, pace_color = "img_slow.png", "🐢", "#28a745"
elif effective_speed < 7.0: img_file, emoji_backup, pace_color = "img_walk.png", "🚶", "#17a2b8"
elif effective_speed < 10.0: img_file, emoji_backup, pace_color = "img_run.png", "🏃", "#ffc107"
else: img_file, emoji_backup, pace_color = "img_rocket.png", "🚀", "#dc3545"

img_base64 = get_img_as_base64(img_file)
avatar_html = f'<img src="data:image/png;base64,{img_base64}" class="avatar-img">' if img_base64 else f'<div class="avatar-text">{emoji_backup}</div>'
st.markdown(f'<div class="avatar-container">{avatar_html}</div>', unsafe_allow_html=True)

percent_speed = min((effective_speed / 15.0) * 100, 100)
st.markdown(f"""
    <div class="gauge-label">
        <span>평균 페이스</span>
        <span style="color:{pace_color}">{effective_speed:.1f} km/h</span>
    </div>
    <div class="gauge-bg">
        <div class="gauge-fill" style="width: {percent_speed}%; background-color: {pace_color};"></div>
    </div>
""", unsafe_allow_html=True)

if journey_progress < 30: progress_color = "#dc3545"
elif journey_progress < 70: progress_color = "#ffc107"
else: progress_color = "#28a745"

st.markdown(f"""
    <div class="gauge-label">
        <span>정류장까지 이동 중...</span>
        <span>🏁</span>
    </div>
    <div class="gauge-bg">
        <div class="gauge-fill" style="width: {journey_progress}%; background-color: {progress_color};"></div>
    </div>
""", unsafe_allow_html=True)


st.divider()


# 7. 최종 결과 (계산 로직)
remain_distance = calculate_distance(current_user_coords[0], current_user_coords[1], dest_coords[0], dest_coords[1])

if remain_distance < 0.02: 
    required_time = 0
    journey_progress = 100 
else:
    required_time = (remain_distance / effective_speed) * 60

inflow_rate = 3.0 # 분당 유입 인원
# [핵심 공식] 현재 대기열 = 기초 대기열(0 or 25) + (시간 * 유입률)
current_queue = base_queue + int(admin_time_passed * inflow_rate)

# 도착 시점의 미래 대기열 = 현재 대기열 + (내가 가는 동안 쌓일 인원)
future_queue = current_queue + (inflow_rate * required_time)
final_bus_time_for_calc = 15 

# 상태 판단
if journey_progress >= 100:
    bg_class, icon, msg, sub_msg = "arrival-bg", "🏁", "도착 완료", "정류장에 도착했습니다!"
elif required_time > final_bus_time_for_calc:
    bg_class, icon, msg, sub_msg = "danger-bg", "🔴", "탑승 불가", f"이미 버스가 떠납니다"
elif future_queue > admin_seats: 
    bg_class, icon, msg, sub_msg = "danger-bg", "🔴", "탑승 불가", f"줄이 너무 깁니다 (잔여 {admin_seats}석)"
elif future_queue > (admin_seats - 5): 
    bg_class, icon, msg, sub_msg = "warning-bg", "🟡", "전력 질주!", f"지금 뛰면 막차 가능"
else:
    bg_class, icon, msg, sub_msg = "success-bg", "🟢", "여유 있음", f"편안하게 가세요"

# HTML 렌더링
html_content = textwrap.dedent(f"""
<div class="status-box {bg_class}">
    <div style="font-size: 50px; margin-bottom: 10px;">{icon}</div>
    <h2 style="margin:0; color: inherit; text-shadow: 0 2px 4px rgba(0,0,0,0.1);">{msg}</h2>
    <p style="margin-top: 5px; font-size: 18px; color: inherit; font-weight: 500;">{sub_msg}</p>
    <div class="status-detail-container">
        <div class="detail-item-box">
            <span class="d-label">버스 도착</span>
            <span class="d-val">{final_bus_time_for_calc}분 후</span>
        </div>
        <div class="detail-divider"></div>
        <div class="detail-item-box">
            <span class="d-label">잔여 좌석</span>
            <span class="d-val">{admin_seats}석</span>
        </div>
        <div class="detail-divider"></div>
        <div class="detail-item-box">
            <span class="d-label">예상 대기</span>
            <span class="d-val">{int(future_queue)}명</span>
        </div>
    </div>
    <div class="summary-row">
        <div>🏁 남은 거리 <b>{int(remain_distance*1000)}m</b></div>
        <div>⏱️ 도착 예정 <b>{format_time(required_time)}</b></div>
    </div>
</div>
""")

st.markdown(html_content, unsafe_allow_html=True)
