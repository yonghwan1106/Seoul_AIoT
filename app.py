import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import json
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

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
    try:
        response = requests.get(API_URL)
        data = response.json()
        if 'IotVdata017' in data and 'row' in data['IotVdata017']:
            df = pd.DataFrame(data['IotVdata017']['row'])
            # 필요한 컬럼이 있는지 확인
            required_columns = ['AVG_TEMP', 'AVG_ULTRA_RAYS', 'AVG_WIND_SPEED', 'AVG_HUMI']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                st.warning(f"다음 컬럼이 데이터에 없습니다: {', '.join(missing_columns)}")
            return df
        else:
            st.error("API 응답에서 예상한 데이터 구조를 찾을 수 없습니다.")
            return pd.DataFrame()  # 빈 DataFrame 반환
    except Exception as e:
        st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")
        return pd.DataFrame()  # 빈 DataFrame 반환

# 사용자 프로필 관리 함수
def load_profile(username):
    if os.path.exists(f"{username}.json"):
        with open(f"{username}.json", "r") as f:
            return json.load(f)
    return None

def save_profile(username, data):
    with open(f"{username}.json", "w") as f:
        json.dump(data, f)


# 카드 생성 함수
def create_card(title, value, min_value, max_value, unit):
    value_str = f"{value:.1f}" if isinstance(value, (int, float)) else str(value)
    min_value_str = f"{min_value:.1f}" if isinstance(min_value, (int, float)) else str(min_value)
    max_value_str = f"{max_value:.1f}" if isinstance(max_value, (int, float)) else str(max_value)
    
    st.markdown(f"""
    <div class="card">
        <h4>{title}</h4>
        <p class="metric-value">{value_str}{unit}</p>
        <p class="metric-label">최소: {min_value_str}{unit} / 최대: {max_value_str}{unit}</p>
    </div>
    """, unsafe_allow_html=True)

# 운동 추천 함수 (확장)
def recommend_exercise(temp, uv, wind_speed, health_status, age, bmi):
    base_recommendation = ""
    if health_status == '양호':
        if 15 <= temp <= 25 and uv < 6:
            base_recommendation = '날씨가 좋습니다. 공원에서 30분 조깅을 추천합니다.'
        else:
            base_recommendation = '실내에서 요가나 스트레칭을 추천합니다.'
    elif health_status == '알레르기':
        if wind_speed < 3:
            base_recommendation = '바람이 약해 알레르기 유발 물질이 적습니다. 가벼운 산책을 추천합니다.'
        else:
            base_recommendation = '알레르기 증상이 악화될 수 있습니다. 실내 운동을 추천합니다.'
    else:
        base_recommendation = '건강 상태를 고려하여 실내에서 가벼운 운동을 추천합니다. 운동 전 의사와 상담하세요.'
    
    # 나이와 BMI를 고려한 추가 권장사항
    if age > 60:
        base_recommendation += " 고령자의 경우 저강도 운동을 권장합니다."
    if bmi > 25:
        base_recommendation += " 체중 관리를 위해 유산소 운동을 늘리는 것이 좋습니다."
    elif bmi < 18.5:
        base_recommendation += " 근력 운동을 통해 체중 증가를 도모하는 것이 좋습니다."
    
    return base_recommendation

# 머신러닝 모델 훈련 및 예측 함수
def train_and_predict(data, user_data):
    # 특성과 타겟 설정
    features = ['AVG_TEMP', 'AVG_HUMI', 'AVG_WIND_SPEED', 'AVG_ULTRA_RAYS']
    target = 'health_score'  # 가상의 건강 점수 (실제 데이터에 맞게 조정 필요)

    # 데이터 준비 (실제 구현 시에는 적절한 데이터 준비 과정 필요)
    X = data[features]
    y = data[target]

    # 데이터 분할
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 스케일링
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 모델 훈련
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train_scaled, y_train)

    # 사용자 데이터로 예측
    user_features = scaler.transform([[user_data['AVG_TEMP'], user_data['AVG_HUMI'], 
                                       user_data['AVG_WIND_SPEED'], user_data['AVG_ULTRA_RAYS']]])
    prediction = model.predict(user_features)

    return prediction[0]

# 메인 앱
def main():
    st.title('🌿 그린 웰니스 트래커')

    # 데이터 로드
    df = fetch_data()
    
    if df.empty:
        st.error("데이터를 불러올 수 없습니다. 잠시 후 다시 시도해 주세요.")
        return  # 함수 종료

    # 최신 데이터 선택
    latest_data = df.iloc[0]

    # 데이터 구조 확인
    st.write("Latest Data:", latest_data)

    # 사이드바 - 사용자 정보
    st.sidebar.header('👤 사용자 정보')
    username = st.sidebar.text_input('사용자명')
    if username:
        user_data = load_profile(username)
        if user_data:
            st.sidebar.success(f"환영합니다, {username}님!")
            user_age = user_data['age']
            user_health = user_data['health_status']
            user_height = user_data['height']
            user_weight = user_data['weight']
        else:
            st.sidebar.warning("새로운 사용자입니다. 정보를 입력해주세요.")
            user_age = st.sidebar.number_input('나이', min_value=1, max_value=120)
            user_health = st.sidebar.selectbox('건강 상태', ['양호', '알레르기', '호흡기 질환', '심장 질환'])
            user_height = st.sidebar.number_input('키 (cm)', min_value=100, max_value=250)
            user_weight = st.sidebar.number_input('체중 (kg)', min_value=30, max_value=200)
            if st.sidebar.button('프로필 저장'):
                save_profile(username, {
                    'age': user_age,
                    'health_status': user_health,
                    'height': user_height,
                    'weight': user_weight
                })
                st.sidebar.success("프로필이 저장되었습니다!")
    else:
        st.sidebar.warning("사용자명을 입력해주세요.")

    # BMI 계산
    if username and user_data:
        bmi = user_weight / ((user_height/100) ** 2)
        st.sidebar.info(f"BMI: {bmi:.2f}")

    # 메인 컨텐츠
    st.header('📊 현재 환경 정보')
    col1, col2, col3, col4 = st.columns(4)

    st.write("Latest Data:", latest_data)
    st.write("AVG_WIND_SPEED type:", type(latest_data.get('AVG_WIND_SPEED')))
    st.write("AVG_WIND_SPEED value:", latest_data.get('AVG_WIND_SPEED'))

    with col1:
        create_card("🌡️ 온도", float(latest_data['AVG_TEMP']), float(latest_data['MIN_TEMP']), float(latest_data['MAX_TEMP']), "°C")
    with col2:
        try:
            avg_wind_speed = float(latest_data.get('AVG_WIND_SPEED', 0))
            min_wind_speed = float(latest_data.get('MIN_WIND_SPEED', 0))
            max_wind_speed = float(latest_data.get('MAX_WIND_SPEED', 0))
        except ValueError:
            st.error("풍속 데이터를 숫자로 변환할 수 없습니다.")
            avg_wind_speed = min_wind_speed = max_wind_speed = "N/A"

        create_card("💨 풍속", avg_wind_speed, min_wind_speed, max_wind_speed, "m/s")
    with col3:
        create_card("💧 습도", float(latest_data['AVG_HUMI']), float(latest_data['MIN_HUMI']), float(latest_data['MAX_HUMI']), "%")
    with col4:
        try:
            avg_uv = float(latest_data.get('AVG_ULTRA_RAYS', 0))
            min_uv = float(latest_data.get('MIN_ULTRA_RAYS', 0))
            max_uv = float(latest_data.get('MAX_ULTRA_RAYS', 0))
        except (ValueError, TypeError):
            st.error("자외선 데이터를 숫자로 변환할 수 없습니다.")
            avg_uv = min_uv = max_uv = "N/A"

        create_card("☀️ 자외선", avg_uv, min_uv, max_uv, "UV")

    # 건강 조언
    st.header('💡 건강 조언')
    try:
        temp = float(latest_data.get('AVG_TEMP', 0))
        uv = float(latest_data.get('AVG_ULTRA_RAYS', 0))
    except (ValueError, TypeError):
        st.error("온도 또는 자외선 데이터를 숫자로 변환할 수 없습니다.")
        temp = uv = 0  # 기본값 설정

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

    # 여러 공원 데이터 비교
    st.header('🌳 공원 데이터 비교')
    parks = df['ADMINISTRATIVE_DISTRICT'].unique()
    selected_parks = st.multiselect('비교할 공원 선택', parks)
    
    if selected_parks:
        compare_data = df[df['ADMINISTRATIVE_DISTRICT'].isin(selected_parks)]
        fig = px.bar(compare_data, x='ADMINISTRATIVE_DISTRICT', y=['AVG_TEMP', 'AVG_HUMI', 'AVG_WIND_SPEED', 'AVG_ULTRA_RAYS'],
                     title='선택된 공원들의 환경 데이터 비교',
                     labels={'value': '측정값', 'variable': '환경 요소'})
        st.plotly_chart(fig, use_container_width=True)


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

    # 머신러닝 모델을 통한 건강 예측
    st.header('🤖 AI 건강 예측')
    health_prediction = train_and_predict(df, latest_data)
    st.success(f"AI 모델이 예측한 당신의 오늘 건강 점수: {health_prediction:.2f}/10")
    st.caption("이 점수는 현재 환경 조건과 당신의 건강 정보를 바탕으로 예측된 값입니다.")
    
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