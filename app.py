import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# 페이지 설정
st.set_page_config(page_title="그린 웰니스 트래커", page_icon="🌿", layout="wide")

# API 설정
API_KEY = '6e4d6c464273616e35345346484678'
API_URL = f'http://openapi.seoul.go.kr:8088/{API_KEY}/json/IotVdata017/1/1000/'

# CSS 스타일
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6
    }
    .main {
        background: #ffffff;
        padding: 3rem;
        border-radius: 1rem;
        box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15) !important;
    }
    .card {
        background: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.1) !important;
        transition: transform 0.3s;
    }
    .card:hover {
        transform: translateY(-5px);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #2e59d9;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #858796;
    }
    .sidebar .sidebar-content {
        background: #4e73df;
    }
    .widget-label {
        color: white !important;
    }
    .stButton>button {
        color: #ffffff;
        background-color: #4e73df;
        border: none;
        border-radius: 0.3rem;
        padding: 0.5rem 1rem;
        font-size: 1rem;
    }
    .stTextInput>div>div>input {
        color: #6e707e;
    }
    h1, h2, h3 {
        color: #5a5c69 !important;
    }
</style>
""", unsafe_allow_html=True)

# 데이터 가져오기
@st.cache_data(ttl=3600)
def fetch_data():
    response = requests.get(API_URL)
    data = response.json()
    return pd.DataFrame(data['IotVdata017']['row'])

# 카드 생성 함수
def create_card(title, value, min_value, max_value, unit):
    st.markdown(f"""
    <div class="card">
        <h4>{title}</h4>
        <p class="metric-value">{value:.1f}{unit}</p>
        <p class="metric-label">최소: {min_value:.1f}{unit} / 최대: {max_value:.1f}{unit}</p>
    </div>
    """, unsafe_allow_html=True)

# 운동 추천 함수
def recommend_exercise(temp, uv, wind_speed, health_status):
    if health_status == '양호':
        if 15 <= temp <= 25 and uv < 6:
            return '날씨가 좋습니다. 공원에서 30분 조깅을 추천합니다.'
        else:
            return '실내에서 요가나 스트레칭을 추천합니다.'
    elif health_status == '알레르기':
        if wind_speed < 3:
            return '바람이 약해 알레르기 유발 물질이 적습니다. 가벼운 산책을 추천합니다.'
        else:
            return '알레르기 증상이 악화될 수 있습니다. 실내 운동을 추천합니다.'
    else:
        return '건강 상태를 고려하여 실내에서 가벼운 운동을 추천합니다. 운동 전 의사와 상담하세요.'

# 메인 앱
def main():
    st.title('🌿 그린 웰니스 트래커')

    # 데이터 로드
    df = fetch_data()
    
    # 최신 데이터 선택
    latest_data = df.iloc[0]

    # 사이드바 - 사용자 정보
    st.sidebar.header('👤 사용자 정보')
    user_name = st.sidebar.text_input('이름')
    user_age = st.sidebar.number_input('나이', min_value=1, max_value=120)
    user_health = st.sidebar.selectbox('건강 상태', ['양호', '알레르기', '호흡기 질환', '심장 질환'])

    # 메인 컨텐츠
    st.header('📊 현재 환경 정보')
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        create_card("🌡️ 온도", float(latest_data['AVG_TEMP']), float(latest_data['MIN_TEMP']), float(latest_data['MAX_TEMP']), "°C")
    with col2:
        create_card("💨 풍속", float(latest_data['AVG_WIND_SPEED']), float(latest_data['MIN_WIND_SPEED']), float(latest_data['MAX_WIND_SPEED']), "m/s")
    with col3:
        create_card("💧 습도", float(latest_data['AVG_HUMI']), float(latest_data['MIN_HUMI']), float(latest_data['MAX_HUMI']), "%")
    with col4:
        create_card("☀️ 자외선", float(latest_data['AVG_ULTRA_RAYS']), float(latest_data['MIN_ULTRA_RAYS']), float(latest_data['MAX_ULTRA_RAYS']), "UV")

    # 건강 조언
    st.header('💡 건강 조언')
    temp = float(latest_data['AVG_TEMP'])
    uv = float(latest_data['AVG_ULTRA_RAYS'])
    
    advice_col1, advice_col2 = st.columns(2)
    with advice_col1:
        if temp > 30:
            st.warning('🔥 현재 기온이 높습니다. 충분한 수분 섭취와 그늘에서의 휴식을 권장합니다.')
        elif temp < 10:
            st.info('❄️ 현재 기온이 낮습니다. 따뜻한 옷차림과 충분한 보온을 권장합니다.')
        else:
            st.success('✅ 현재 기온이 적당합니다. 가벼운 운동을 하기 좋은 날씨입니다.')
    
    with advice_col2:
        if uv > 6:
            st.warning('☀️ 자외선 지수가 높습니다. 자외선 차단제를 바르고 모자를 착용하세요.')
        else:
            st.success('✅ 자외선 지수가 적당합니다.')

    # 시계열 데이터 시각화
    st.header('📈 최근 환경 데이터 추이')
    df['SENSING_TIME'] = pd.to_datetime(df['SENSING_TIME'])
    df = df.sort_values('SENSING_TIME')

    # 최근 24시간 데이터만 선택
    last_24h = datetime.now() - timedelta(hours=24)
    df_last_24h = df[df['SENSING_TIME'] > last_24h]

    fig = px.line(df_last_24h, x='SENSING_TIME', y=['AVG_TEMP', 'AVG_HUMI', 'AVG_WIND_SPEED', 'AVG_ULTRA_RAYS'],
                  labels={'value': '측정값', 'variable': '환경 요소'},
                  title='최근 24시간 환경 데이터 추이')
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#5a5c69")
    )
    st.plotly_chart(fig, use_container_width=True)

    # 맞춤형 운동 추천
    st.header('🏃‍♀️ 오늘의 운동 추천')
    exercise_recommendation = recommend_exercise(temp, uv, float(latest_data['AVG_WIND_SPEED']), user_health)
    st.info(exercise_recommendation)

    # 공원 선택 및 정보 표시
    st.header('🌳 공원 정보')
    parks = df['ADMINISTRATIVE_DISTRICT'].unique()
    selected_park = st.selectbox('공원 선택', parks)
    
    park_data = df[df['ADMINISTRATIVE_DISTRICT'] == selected_park].iloc[0]
    
    park_col1, park_col2 = st.columns(2)
    with park_col1:
        st.markdown(f"**선택한 공원:** {selected_park}")
        st.markdown(f"**위치:** {park_data['ADMINISTRATIVE_DISTRICT']}")
    with park_col2:
        st.markdown(f"**현재 온도:** {park_data['AVG_TEMP']}°C")
        st.markdown(f"**현재 습도:** {park_data['AVG_HUMI']}%")

    # 사용자 피드백
    st.header('💬 피드백')
    feedback = st.text_area('앱 사용 경험을 공유해주세요:')
    if st.button('제출'):
        st.success('피드백이 제출되었습니다. 감사합니다!')

if __name__ == '__main__':
    main()