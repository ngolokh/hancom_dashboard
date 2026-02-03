import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 설정
# pylint: disable=non-ascii-name
종목명 = "한글과컴퓨터"
종목코드 = "030520.KQ"
START_DATE = "2025-01-01"
END_DATE = "2025-12-31"

# 데이터 다운로드 및 CSV 저장 (사용자 요청 코드 적용)
print(f"\n{'='*50}")
print(f"{종목명}({종목코드}) 데이터 다운로드 시작...")
print(f"기간: {START_DATE} ~ {END_DATE}")
print(f"{'='*50}\n")

try:
    df = yf.download(종목코드, start=START_DATE, end=END_DATE)

    if not df.empty:
        FILENAME = f"{종목코드.replace('.', '_')}_2025.csv"
        df.to_csv(FILENAME, encoding='utf-8-sig')

        print("✓ 다운로드 성공!")
        print(f"✓ 데이터 개수: {len(df)}개")
        print(f"✓ 저장 파일: {FILENAME}")
        print("\n데이터 미리보기:")
        print(df.head())
        print("\n기본 통계:")
        print(df['Close'].describe())
    else:
        print("✗ 데이터가 없습니다. 종목코드를 확인해주세요.")
        exit()

except Exception as e: # pylint: disable=broad-exception-caught
    print(f"✗ 오류 발생: {e}")
    print("종목코드 형식을 확인해주세요 (예: 035420.KS, 304100.KQ)")
    exit()

print(f"\n{'='*50}")

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 페이지 설정 (넓은 화면 모드)
st.set_page_config(layout="wide", page_title="한글과컴퓨터 분석")

# 2. 데이터 로드 및 전처리
@st.cache_data #데이터를 캐시에 저장하는 함수, 캐ㅇ은 데이터 로딩시간을 줄여줌
def get_data():
    # 파일 구조에 따라 상단 2개 행(Ticker, Empty Date row) 제외
    df = pd.read_csv('data/030520_KQ_2025.csv', skiprows=[1, 2])
    df.rename(columns={'Price': 'Date'}, inplace=True) # 'Price' 컬럼의 이름을 'Date'로 변경
    df['Date'] = pd.to_datetime(df['Date'])
    
    # 이동평균선 추가 (특정기간 주가의 평균값을 계산해 선으로 그린 그래프, 주의 전반적인 방향성이나 흐름이 바뀌는 추이를 파악하기 위해 고안)
    df['MA5'] = df['Close'].rolling(window=5).mean() #5일선 : 주식은 주중에만 열려 1주일간의 주가 평균
    df['MA20'] = df['Close'].rolling(window=20).mean() # 20일선 : 같은 셈법으로 한달
    
    #
    
    # 등락폭(Difference) 계산 (현재가격 - 기준가격(보통 전일 종가)
    df['Diff'] = df['Close'].diff()
    return df

df = get_data()

# 3. 상단 타이틀 및 KPI
st.title("📊 한글과컴퓨터 (030520.KQ) 주가 대시보드")
st.markdown("---")

# --- 레이아웃 : 위(차트) / 아래(데이터) 구조 ---

# 1. 상단 차트 영역
st.subheader("📈 주가 및 거래량 추세")

# 서브플롯 생성 (비율 및 간격 최적화)
#figure = 그래프가 그려지는 화면
#subplot = 그래프

fig = make_subplots(
    rows=2, cols=1, 
    shared_xaxes=True, 
    vertical_spacing=0.03,    # 차트 간 간격 최소화
    row_heights=[0.75, 0.25]
)

# 차트 데이터 추가
fig.add_trace(go.Candlestick(
    x=df['Date'], open=df['Open'], high=df['High'],
    low=df['Low'], close=df['Close'], name="주가",
    increasing_line_color='red', decreasing_line_color='blue'
), row=1, col=1)

fig.add_trace(go.Scatter(x=df['Date'], y=df['MA5'], name='5일선', line=dict(color='purple', width=1)), row=1, col=1)
fig.add_trace(go.Scatter(x=df['Date'], y=df['MA20'], name='20일선', line=dict(color='green', width=1)), row=1, col=1)
fig.add_trace(go.Bar(x=df['Date'], y=df['Volume'], name='거래량', marker_color='grey'), row=2, col=1)

# Y축 원화 표시 및 레이아웃 설정
fig.update_yaxes(tickformat=',d', ticksuffix='원 ', row=1, col=1)
fig.update_yaxes(tickformat=',d', row=2, col=1)

fig.update_layout(
    height=600, 
    xaxis_rangeslider_visible=False, 
    margin=dict(l=80, r=20, t=20, b=20),
    hovermode='x unified',
    dragmode='pan',
    template='plotly_white',
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1) # 범례를 상단으로
)

# 차트 출력 (휠 줌 활성화)
st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})

# --- 데이터 필터링 기능 추가 ---

st.markdown("---")
st.subheader("🔍 데이터 필터링")

# 필터 레이아웃 (3컬럼)
f_col1, f_col2, f_col3 = st.columns([2, 2, 3])

with f_col1:
    # 1. 기간 선택 필터
    start_date = st.date_input("시작일", value=df['Date'].min(), min_value=df['Date'].min(), max_value=df['Date'].max())
with f_col2:
    end_date = st.date_input("종료일", value=df['Date'].max(), min_value=df['Date'].min(), max_value=df['Date'].max())
with f_col3:
    # 2. 등락 필터
    status_filter = st.selectbox("변동성 선택", ["전체", "상승(▲)", "하락(▼)", "보합(-)"])

# --- 필터링 로직 적용 ---
# 1. 기간 필터 적용
filtered_df = df[(df['Date'].dt.date >= start_date) & (df['Date'].dt.date <= end_date)].copy()

# 2. 등락 필터 적용 (Diff 컬럼 활용)
if status_filter == "상승(▲)":
    filtered_df = filtered_df[filtered_df['Diff'] > 0]
elif status_filter == "하락(▼)":
    filtered_df = filtered_df[filtered_df['Diff'] < 0]
elif status_filter == "보합(-)":
    filtered_df = filtered_df[filtered_df['Diff'] == 0]

# --- 하단 테이블 출력 ---
st.write(f"총 **{len(filtered_df)}**건의 데이터가 검색되었습니다.")

# 출력용 데이터 가공
display_df = filtered_df[['Date', 'Close', 'Diff', 'Volume']].copy()
display_df = display_df.sort_values(by='Date', ascending=False)
display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d')

def highlight_diff(val):
    if val > 0: return 'color: red'
    elif val < 0: return 'color: blue'
    return 'color: black'

st.dataframe(
    display_df.style.format({'Close': '{:,.0f}', 'Diff': '{:+,.0f}', 'Volume': '{:,.0f}'})
              .map(highlight_diff, subset=['Diff']),
    use_container_width=True,
    height=400
)

