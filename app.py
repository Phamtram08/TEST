# app.py - Hệ thống Tự động hóa Báo cáo Tài chính
# Tương thích Python 3.13

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
import requests
import io
import warnings
warnings.filterwarnings('ignore')

# Cấu hình trang - PHẢI ĐẶT ĐẦU TIÊN
st.set_page_config(
    page_title="Auto Financial Reporting",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    /* Header chính */
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #0a2647, #1e3c72);
        color: white;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .main-header p {
        font-size: 1.2rem;
        opacity: 0.9;
    }
    
    /* Card metrics */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        border: 1px solid #eef2f6;
        transition: transform 0.3s;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    
    /* Sidebar */
    .sidebar-header {
        padding: 1rem;
        background: #1e3c72;
        color: white;
        border-radius: 10px;
        margin-bottom: 1rem;
        text-align: center;
        font-weight: bold;
    }
    
    /* Button */
    .stButton > button {
        background: linear-gradient(90deg, #0a2647, #1e3c72);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 25px;
        font-weight: 600;
        transition: all 0.3s;
        width: 100%;
    }
    .stButton > button:hover {
        background: linear-gradient(90deg, #1b4a7a, #2a5f9e);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        transform: scale(1.02);
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem 0;
        color: #64748b;
        border-top: 1px solid #eef2f6;
        margin-top: 3rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>📊 HỆ THỐNG TỰ ĐỘNG HÓA BÁO CÁO TÀI CHÍNH</h1>
    <p>Python 3.13 🤝 Streamlit | Yahoo Finance | Phân tích đa nguồn | Báo cáo thông minh</p>
</div>
""", unsafe_allow_html=True)

# Khởi tạo session state
if 'data' not in st.session_state:
    st.session_state.data = None
if 'data_source' not in st.session_state:
    st.session_state.data_source = None
if 'symbol' not in st.session_state:
    st.session_state.symbol = "AAPL"

# ==================== FUNCTIONS ====================
@st.cache_data(ttl=3600)
def fetch_yahoo_data(symbol, period="1y"):
    """Lấy dữ liệu từ Yahoo Finance với caching"""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        
        if not df.empty:
            df.reset_index(inplace=True)
            # Đổi tên cột cho dễ đọc
            df.columns = [col.replace(' ', '_') for col in df.columns]
            
            # Tính các chỉ số kỹ thuật
            df['Daily_Return'] = df['Close'].pct_change() * 100
            df['MA20'] = df['Close'].rolling(window=20).mean()
            df['MA50'] = df['Close'].rolling(window=50).mean()
            df['Volume_MA'] = df['Volume'].rolling(window=5).mean()
            
            return df, f"Yahoo Finance - {symbol.upper()}"
    except Exception as e:
        return None, str(e)
    return None, "Không có dữ liệu"

@st.cache_data(ttl=86400)
def fetch_worldbank_data(country, indicator, start_year, end_year):
    """Lấy dữ liệu từ World Bank API"""
    try:
        url = f"http://api.worldbank.org/v2/country/{country}/indicator/{indicator}"
        params = {
            'format': 'json',
            'date': f"{start_year}:{end_year}",
            'per_page': 1000
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if len(data) > 1 and data[1]:
            records = []
            for item in data[1]:
                if item['value'] is not None:
                    records.append({
                        'Năm': int(item['date']),
                        'Giá_trị': float(item['value'])
                    })
            
            if records:
                df = pd.DataFrame(records)
                df = df.sort_values('Năm')
                return df, f"World Bank - {country}"
    except Exception as e:
        return None, str(e)
    return None, "Không có dữ liệu"

def generate_income_statement(df):
    """Tạo báo cáo kết quả kinh doanh"""
    if 'Date' not in df.columns or 'Close' not in df.columns:
        return None
    
    # Tạo bản sao để tránh warning
    df_copy = df.copy()
    df_copy['Year'] = pd.to_datetime(df_copy['Date']).dt.year
    
    # Tổng hợp theo năm
    yearly = df_copy.groupby('Year').agg({
        'Close': ['sum', 'mean', 'min', 'max']
    }).round(2)
    
    yearly.columns = ['Doanh_thu', 'Gia_TB', 'Thap_nhat', 'Cao_nhat']
    yearly = yearly.reset_index()
    
    # Tính các chỉ số tài chính
    yearly['Gia_von'] = yearly['Doanh_thu'] * 0.65
    yearly['Loi_nhuan_gop'] = yearly['Doanh_thu'] - yearly['Gia_von']
    yearly['Chi_phi_HD'] = yearly['Doanh_thu'] * 0.15
    yearly['LN_HDKD'] = yearly['Loi_nhuan_gop'] - yearly['Chi_phi_HD']
    yearly['LN_sau_thue'] = yearly['LN_HDKD'] * 0.8
    yearly['Bien_LN'] = (yearly['LN_sau_thue'] / yearly['Doanh_thu'] * 100).round(2)
    
    return yearly

def generate_cash_flow(df):
    """Tạo báo cáo dòng tiền"""
    if not all(col in df.columns for col in ['Date', 'Volume', 'Close']):
        return None
    
    df_copy = df.copy()
    df_copy['Date'] = pd.to_datetime(df_copy['Date'])
    df_copy['YearMonth'] = df_copy['Date'].dt.to_period('M').astype(str)
    df_copy['Gia_tri_GD'] = df_copy['Close'] * df_copy['Volume']
    
    monthly = df_copy.groupby('YearMonth').agg({
        'Gia_tri_GD': 'sum',
        'Volume': 'sum',
        'Close': 'mean'
    }).round(2)
    monthly = monthly.reset_index()
    
    # Tính dòng tiền
    monthly['CF_HDKD'] = monthly['Gia_tri_GD'] * 0.7
    monthly['CF_Dau_tu'] = -monthly['Gia_tri_GD'] * 0.2
    monthly['CF_Tai_chinh'] = -monthly['Gia_tri_GD'] * 0.1
    monthly['CF_thuan'] = (monthly['CF_HDKD'] + monthly['CF_Dau_tu'] + 
                           monthly['CF_Tai_chinh'])
    
    return monthly

# ==================== SIDEBAR ====================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/stocks.png", width=80)
    st.markdown('<p class="sidebar-header">🔍 KẾT NỐI DỮ LIỆU</p>', unsafe_allow_html=True)
    
    # Chọn nguồn dữ liệu
    data_source = st.radio(
        "🌐 Nguồn dữ liệu:",
        ["Yahoo Finance (Chứng khoán)", 
         "World Bank (Kinh tế vĩ mô)",
         "Tải file lên (CSV/Excel)"]
    )
    
    # ===== YAHOO FINANCE =====
    if data_source == "Yahoo Finance (Chứng khoán)":
        st.subheader("📈 Cấu hình Yahoo Finance")
        
        # Popular stocks
        popular_stocks = {
            "US Stocks": ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "JPM", "V", "WMT"],
            "Vietnam Stocks": ["VCB", "BID", "CTG", "ACB", "VIC", "VHM", "VNM", "HPG", "FPT", "MSN"],
            "Indices": ["^VNINDEX", "^GSPC", "^IXIC", "^DJI"]
        }
        
        category = st.selectbox("Danh mục:", list(popular_stocks.keys()))
        symbol = st.selectbox("Mã chứng khoán:", popular_stocks[category])
        
        # Custom symbol
        custom_symbol = st.text_input("Hoặc nhập mã khác:", "").upper()
        if custom_symbol:
            symbol = custom_symbol
        
        # Time period
        period = st.selectbox(
            "Kỳ gian:",
            ["1mo", "3mo", "6mo", "1y", "2y", "5y", "ytd", "max"],
            index=3  # Default 1y
        )
        
        if st.button("📥 Lấy dữ liệu", use_container_width=True):
            with st.spinner(f"Đang tải dữ liệu {symbol}..."):
                df, message = fetch_yahoo_data(symbol, period)
                if df is not None:
                    st.session_state.data = df
                    st.session_state.data_source = message
                    st.session_state.symbol = symbol
                    st.success(f"✅ Đã tải {len(df)} bản ghi")
                else:
                    st.error(f"❌ Lỗi: {message}")
    
    # ===== WORLD BANK =====
    elif data_source == "World Bank (Kinh tế vĩ mô)":
        st.subheader("🌍 Cấu hình World Bank")
        
        # Countries
        countries = {
            "VN": "Việt Nam",
            "US": "Hoa Kỳ",
            "CN": "Trung Quốc",
            "JP": "Nhật Bản",
            "KR": "Hàn Quốc",
            "SG": "Singapore",
            "TH": "Thái Lan",
            "ID": "Indonesia",
            "DE": "Đức",
            "FR": "Pháp",
            "UK": "Anh"
        }
        
        country = st.selectbox("Quốc gia:", list(countries.keys()),
                              format_func=lambda x: f"{x} - {countries[x]}")
        
        # Indicators
        indicators = {
            "NY.GDP.MKTP.CD": "GDP (USD)",
            "NY.GDP.PCAP.CD": "GDP bình quân đầu người",
            "FP.CPI.TOTL.ZG": "Lạm phát CPI (%)",
            "SP.POP.TOTL": "Dân số",
            "NE.EXP.GNFS.CD": "Xuất khẩu (USD)",
            "NE.IMP.GNFS.CD": "Nhập khẩu (USD)",
            "BN.CAB.XOKA.CD": "Cán cân thanh toán (USD)"
        }
        
        indicator = st.selectbox("Chỉ số:", list(indicators.keys()),
                                format_func=lambda x: indicators[x])
        
        # Time range
        col1, col2 = st.columns(2)
        with col1:
            start_year = st.number_input("Năm bắt đầu:", min_value=1960, max_value=2024, value=2010)
        with col2:
            end_year = st.number_input("Năm kết thúc:", min_value=1960, max_value=2024, value=2023)
        
        if st.button("📥 Lấy dữ liệu", use_container_width=True):
            with st.spinner("Đang tải dữ liệu..."):
                df, message = fetch_worldbank_data(country, indicator, start_year, end_year)
                if df is not None:
                    st.session_state.data = df
                    st.session_state.data_source = f"World Bank - {countries[country]} - {indicators[indicator]}"
                    st.success(f"✅ Đã tải {len(df)} bản ghi")
                else:
                    st.error(f"❌ Lỗi: {message}")
    
    # ===== UPLOAD FILE =====
    else:
        st.subheader("📁 Tải file lên")
        st.info("Hỗ trợ: CSV, Excel")
        
        uploaded_file = st.file_uploader(
            "Chọn file:", 
            type=['csv', 'xlsx', 'xls'],
            help="File CSV hoặc Excel có dữ liệu tài chính"
        )
        
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                st.session_state.data = df
                st.session_state.data_source = f"File: {uploaded_file.name}"
                st.success(f"✅ Đã tải {len(df)} dòng, {len(df.columns)} cột")
            except Exception as e:
                st.error(f"❌ Lỗi đọc file: {str(e)}")

# ==================== MAIN CONTENT ====================
if st.session_state.data is not None:
    df = st.session_state.data
    
    # Thông tin nguồn dữ liệu
    st.info(f"📌 **Nguồn:** {st.session_state.data_source} | **Số dòng:** {len(df):,} | **Số cột:** {len(df.columns)}")
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Tổng quan", "📈 Biểu đồ", "📋 Dữ liệu", "📑 Báo cáo TC"])
    
    with tab1:
        st.subheader("📊 TỔNG QUAN DỮ LIỆU")
        
        # Hiển thị 5 dòng đầu
        st.markdown("**5 dòng dữ liệu đầu tiên:**")
        st.dataframe(df.head(), use_container_width=True)
        
        # Thông tin cơ bản
        col1, col2, col3, col4 = st.columns(4)
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        with col1:
            st.metric("Tổng số dòng", f"{len(df):,}")
        
        with col2:
            st.metric("Tổng số cột", len(df.columns))
        
        with col3:
            st.metric("Cột số", len(numeric_cols))
        
        with col4:
            if numeric_cols:
                total_value = df[numeric_cols[0]].sum() if numeric_cols else 0
                st.metric("Tổng giá trị", f"{total_value:,.0f}")
        
        # Thống kê mô tả
        if numeric_cols and st.checkbox("📊 Xem thống kê mô tả"):
            st.dataframe(df[numeric_cols].describe().round(2), use_container_width=True)
    
    with tab2:
        st.subheader("📈 TRỰC QUAN HÓA DỮ LIỆU")
        
        # Kiểm tra có cột số không
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_cols:
            st.warning("⚠️ Không có dữ liệu số để vẽ biểu đồ")
        else:
            # Chọn loại biểu đồ
            chart_type = st.selectbox(
                "Loại biểu đồ:",
                ["Biểu đồ đường", "Biểu đồ cột", "Biểu đồ phân tán", "Histogram"]
            )
            
            # Chọn cột
            cols = df.columns.tolist()
            
            # Tìm cột ngày tháng
            date_cols = [col for col in cols if any(x in col.lower() for x in 
                         ['date', 'time', 'year', 'ngay', 'thang', 'nam'])]
            
            if date_cols and chart_type != "Histogram":
                x_col = st.selectbox("Trục X (thời gian):", date_cols, index=0)
            else:
                x_col = st.selectbox("Trục X:", cols, index=0 if cols else 0)
            
            y_col = st.selectbox("Trục Y:", numeric_cols, index=0)
            
            # Vẽ biểu đồ
            if chart_type == "Biểu đồ đường":
                fig = px.line(df, x=x_col, y=y_col, title=f"{y_col} theo thời gian")
            
            elif chart_type == "Biểu đồ cột":
                fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} theo thời gian")
            
            elif chart_type == "Biểu đồ phân tán":
                if len(numeric_cols) > 1:
                    size_col = st.selectbox("Kích thước:", numeric_cols, index=1 if len(numeric_cols) > 1 else 0)
                    fig = px.scatter(df, x=x_col, y=y_col, size=size_col, 
                                    title=f"Tương quan {y_col} và {size_col}")
                else:
                    fig = px.scatter(df, x=x_col, y=y_col, title=f"Phân tán {y_col}")
            
            else:  # Histogram
                fig = px.histogram(df, x=y_col, nbins=30, title=f"Phân phối {y_col}")
            
            # Hiển thị biểu đồ
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader("📋 DỮ LIỆU CHI TIẾT")
        
        # Tìm kiếm
        search = st.text_input("🔍 Tìm kiếm (gõ nội dung cần tìm):", "")
        
        if search:
            # Tìm trong tất cả các cột
            mask = df.astype(str).apply(lambda x: x.str.contains(search, case=False, na=False)).any(axis=1)
            filtered_df = df[mask]
            st.write(f"Tìm thấy {len(filtered_df)} kết quả")
        else:
            filtered_df = df
        
        # Hiển thị dữ liệu
        st.dataframe(filtered_df, use_container_width=True, height=400)
        
        # Download
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Tải xuống CSV",
            data=csv,
            file_name=f"data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with tab4:
        st.subheader("📑 BÁO CÁO TÀI CHÍNH TỰ ĐỘNG")
        
        # Chọn loại báo cáo
        report_option = st.selectbox(
            "Loại báo cáo:",
            ["Báo cáo kết quả kinh doanh", "Báo cáo dòng tiền", "Phân tích chỉ số"]
        )
        
        if report_option == "Báo cáo kết quả kinh doanh":
            income_stmt = generate_income_statement(df)
            
            if income_stmt is not None:
                st.markdown("### 📊 BÁO CÁO KẾT QUẢ KINH DOANH THEO NĂM")
                
                # Format số
                display_df = income_stmt.copy()
                for col in ['Doanh_thu', 'Gia_von', 'Loi_nhuan_gop', 'LN_sau_thue']:
                    if col in display_df.columns:
                        display_df[col] = display_df[col].apply(lambda x: f"{x:,.0f}")
                
                st.dataframe(display_df, use_container_width=True)
                
                # Biểu đồ
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=income_stmt['Year'], 
                    y=income_stmt['Doanh_thu'],
                    name='Doanh thu',
                    marker_color='#1e3c72'
                ))
                fig.add_trace(go.Bar(
                    x=income_stmt['Year'], 
                    y=income_stmt['LN_sau_thue'],
                    name='Lợi nhuận',
                    marker_color='#2ecc71'
                ))
                fig.add_trace(go.Scatter(
                    x=income_stmt['Year'], 
                    y=income_stmt['Bien_LN'],
                    name='Biên LN %',
                    yaxis='y2',
                    line=dict(color='red', width=3)
                ))
                
                fig.update_layout(
                    title='Doanh thu và Lợi nhuận theo năm',
                    xaxis_title='Năm',
                    yaxis_title='Giá trị',
                    yaxis2=dict(
                        title='Biên lợi nhuận %',
                        overlaying='y',
                        side='right',
                        range=[0, 100]
                    ),
                    barmode='group',
                    height=500,
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ Không đủ dữ liệu để tạo báo cáo KQKD (cần cột Date và Close)")
        
        elif report_option == "Báo cáo dòng tiền":
            cash_flow = generate_cash_flow(df)
            
            if cash_flow is not None:
                st.markdown("### 💰 BÁO CÁO DÒNG TIỀN THEO THÁNG")
                
                # Format
                display_cf = cash_flow.copy()
                for col in display_cf.columns:
                    if col not in ['YearMonth']:
                        display_cf[col] = display_cf[col].apply(lambda x: f"{x:,.0f}")
                
                st.dataframe(display_cf, use_container_width=True)
                
                # Biểu đồ
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=cash_flow['YearMonth'],
                    y=cash_flow['CF_HDKD'],
                    name='HĐKD',
                    marker_color='#2ecc71'
                ))
                fig.add_trace(go.Bar(
                    x=cash_flow['YearMonth'],
                    y=cash_flow['CF_Dau_tu'],
                    name='Đầu tư',
                    marker_color='#e74c3c'
                ))
                fig.add_trace(go.Bar(
                    x=cash_flow['YearMonth'],
                    y=cash_flow['CF_Tai_chinh'],
                    name='Tài chính',
                    marker_color='#f39c12'
                ))
                fig.add_trace(go.Scatter(
                    x=cash_flow['YearMonth'],
                    y=cash_flow['CF_thuan'],
                    name='CF thuần',
                    line=dict(color='#0a2647', width=3),
                    mode='lines+markers'
                ))
                
                fig.update_layout(
                    title='Dòng tiền theo tháng',
                    xaxis_title='Tháng',
                    yaxis_title='Giá trị',
                    barmode='relative',
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ Không đủ dữ liệu (cần cột Date, Volume, Close)")
        
        else:  # Phân tích chỉ số
            st.markdown("### 📈 PHÂN TÍCH CHỈ SỐ TÀI CHÍNH")
            
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if numeric_cols:
                # Tính các chỉ số
                stats_data = []
                for col in numeric_cols:
                    col_data = df[col].dropna()
                    if len(col_data) > 0:
                        mean_val = col_data.mean()
                        std_val = col_data.std()
                        stats_data.append({
                            'Chỉ số': col,
                            'Trung bình': f"{mean_val:,.2f}",
                            'Trung vị': f"{col_data.median():,.2f}",
                            'Độ lệch chuẩn': f"{std_val:,.2f}",
                            'Min': f"{col_data.min():,.2f}",
                            'Max': f"{col_data.max():,.2f}",
                            'Biến động %': f"{(std_val/mean_val*100):,.2f}" if mean_val != 0 else "0.00"
                        })
                
                stats_df = pd.DataFrame(stats_data)
                st.dataframe(stats_df, use_container_width=True)
                
                # Ma trận tương quan
                if len(numeric_cols) > 1:
                    st.markdown("### 📊 MA TRẬN TƯƠNG QUAN")
                    corr = df[numeric_cols].corr()
                    fig = px.imshow(
                        corr,
                        text_auto='.2f',
                        aspect="auto",
                        color_continuous_scale='RdBu_r',
                        title="Tương quan giữa các chỉ số"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ Không có dữ liệu số để phân tích")

else:
    # Hướng dẫn khi chưa có dữ liệu
    st.markdown("""
    <div style="text-align: center; padding: 3rem;">
        <h2>🎯 CHÀO MỪNG ĐẾN VỚI HỆ THỐNG</h2>
        <p style="font-size: 1.2rem; color: #64748b; margin: 2rem 0;">
            Vui lòng chọn nguồn dữ liệu ở sidebar bên trái để bắt đầu
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; background: #f8fafc; border-radius: 10px; height: 250px;">
            <h3 style="color: #0a2647;">📈 Yahoo Finance</h3>
            <p>Dữ liệu chứng khoán, cổ phiếu, chỉ số từ Yahoo Finance</p>
            <p style="color: #1e3c72; font-weight: bold;">👉 Chọn ở sidebar</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; background: #f8fafc; border-radius: 10px; height: 250px;">
            <h3 style="color: #0a2647;">🌍 World Bank</h3>
            <p>Dữ liệu kinh tế vĩ mô: GDP, dân số, xuất nhập khẩu</p>
            <p style="color: #1e3c72; font-weight: bold;">👉 Chọn ở sidebar</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; background: #f8fafc; border-radius: 10px; height: 250px;">
            <h3 style="color: #0a2647;">📁 Upload File</h3>
            <p>Tải lên file CSV hoặc Excel của bạn</p>
            <p style="color: #1e3c72; font-weight: bold;">👉 Chọn ở sidebar</p>
        </div>
        """, unsafe_allow_html=True)

# Footer
st.markdown("""
<div class="footer">
    <p>📊 Hệ thống Tự động hóa Báo cáo Tài chính | Python 3.13 + Streamlit</p>
    <p>Dữ liệu: Yahoo Finance, World Bank | Dự án môn Lập trình Python</p>
    <p>© 2024 - Phát triển bởi Nhóm sinh viên</p>
</div>
""", unsafe_allow_html=True)
