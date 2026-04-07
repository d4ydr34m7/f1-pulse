import streamlit as st
import boto3
import pandas as pd
import time
import math
import plotly.express as px
import plotly.graph_objects as go
from boto3.dynamodb.conditions import Key

# 1. UI Setup
st.set_page_config(page_title="F1 Pitwall", layout="wide", page_icon="🏎️")
st.title("🏎️ Live F1 Telemetry & GPS Tracking")

# 2. AWS Connection
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('f1-live-telemetry')

def get_latest_data(driver):
    try:
        response = table.query(
            KeyConditionExpression=Key('Driver').eq(driver),
            ScanIndexForward=False, 
            Limit=40
        )
        return response.get('Items', [])
    except Exception:
        return []

DRIVER_COLORS = {"HAM": "#00D2BE", "BOT": "#777777"}
DRIVER_ORDER = {"Driver": ["HAM", "BOT"]} 

# 3. Layout Structure
col_map, col_tires = st.columns([2, 1])
with col_map:
    st.subheader("📍 Live Track Position")
    track_map = st.empty()
with col_tires:
    st.subheader("🛞 Tire Heatmap")
    th_ham, th_bot = st.columns(2)
    tire_ham, tire_bot = th_ham.empty(), th_bot.empty()

st.divider()

col_speed, col_rpm, col_throttle = st.columns(3)
with col_speed:
    st.subheader("🏎️ Speed (km/h)")
    s_h, s_b = st.columns(2)
    ham_speed, bot_speed, speed_chart = s_h.empty(), s_b.empty(), st.empty()
with col_rpm:
    st.subheader("⚙️ Engine RPM")
    r_h, r_b = st.columns(2)
    ham_rpm, bot_rpm, rpm_chart = r_h.empty(), r_b.empty(), st.empty()
with col_throttle:
    st.subheader("🚥 Throttle %")
    t_h, t_b = st.columns(2)
    ham_throttle, bot_throttle, throttle_chart = t_h.empty(), t_b.empty(), st.empty()

# 4. Helper Functions
def format_line_chart(fig, current_df):
    if current_df.empty: return fig
    min_time = current_df['Timestamp'].min()
    max_time = current_df['Timestamp'].max() + pd.Timedelta(seconds=4)
    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10), height=280,
        xaxis_title=None, yaxis_title=None,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=None),
        uirevision="constant", template="plotly_dark"
    )
    fig.update_xaxes(showgrid=False, range=[min_time, max_time])
    return fig

def draw_car_heatmap(driver, is_losing_traction):
    # 1. Coordinates for the 4 tires (FL, FR, RL, RR)
    x_coords = [0.3, 0.7, 0.3, 0.7]
    y_coords = [0.8, 0.8, 0.2, 0.2]
    
    # 2. Colors and Hover Text
    base_color = DRIVER_COLORS[driver]
    rear_color = "#FF0000" if is_losing_traction else base_color
    colors = [base_color, base_color, rear_color, rear_color]
    
    status = "⚠️ Traction Loss" if is_losing_traction else "✅ Optimal"
    hover_text = [
        "Front Left: Optimal", 
        "Front Right: Optimal", 
        f"Rear Left: {status}", 
        f"Rear Right: {status}"
    ]
    
    # 3. Draw the tires with Labels inside them
    fig = go.Figure(go.Scatter(
        x=x_coords, y=y_coords, 
        mode='markers+text', 
        text=['FL', 'FR', 'RL', 'RR'], # Labels
        textposition="middle center",
        textfont=dict(color='white', size=10, weight='bold'),
        hoverinfo="text",
        hovertext=hover_text,
        marker=dict(symbol='square', size=40, color=colors, line=dict(width=1, color='rgba(255,255,255,0.2)'))
    ))
    
    # 4. Add a dynamic subtitle to explain the color
    status_text = "<span style='color:#FF0000'>🔴 Wheel Slip</span>" if is_losing_traction else "<span style='color:#00D2BE'>🟢 Optimal Grip</span>"
    title_text = f"<b>{driver}</b><br><span style='font-size:12px'>{status_text}</span>"
    
    fig.update_layout(
        title=dict(text=title_text, x=0.5, y=0.9, xanchor='center'),
        xaxis=dict(range=[0, 1], visible=False), 
        yaxis=dict(range=[0, 1], visible=False),
        margin=dict(l=0, r=0, t=50, b=0), 
        height=190, 
        plot_bgcolor='rgba(0,0,0,0)', 
        paper_bgcolor='rgba(0,0,0,0)', 
        uirevision="constant"
    )
    return fig

# 5. Real-Time Loop
loop_count = 0
while True:
    loop_count += 1
    ham_items, bot_items = get_latest_data("HAM"), get_latest_data("BOT")
    all_items = ham_items + bot_items
    
    if all_items:
        latest_ham, latest_bot = (ham_items[0] if ham_items else {}), (bot_items[0] if bot_items else {})
        latest_ham, latest_bot = (ham_items[0] if ham_items else {}), (bot_items[0] if bot_items else {})
                
        # --- Top Metrics ---
        ham_speed.metric("HAM", f"{float(latest_ham.get('Speed', 0)):.1f}")
        bot_speed.metric("BOT", f"{float(latest_bot.get('Speed', 0)):.1f}")
        ham_rpm.metric("HAM", f"{float(latest_ham.get('RPM', 0)):.0f}")
        bot_rpm.metric("BOT", f"{float(latest_bot.get('RPM', 0)):.0f}")
        ham_throttle.metric("HAM", f"{float(latest_ham.get('Throttle', 0)):.0f}%")
        bot_throttle.metric("BOT", f"{float(latest_bot.get('Throttle', 0)):.0f}%")
        
        # --- Clean Data for Charts ---
        df = pd.DataFrame(all_items)
        cols_to_fix = ['Speed', 'RPM', 'Throttle', 'TractionLoss']
        for col in cols_to_fix:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        if 'Timestamp' in df.columns:
            df['Timestamp'] = pd.to_datetime(pd.to_numeric(df['Timestamp'], errors='coerce'), unit='ms')
        
        df = df.dropna(subset=['Speed']).drop_duplicates(subset=['Timestamp', 'Driver']).sort_values(by=['Driver', 'Timestamp'])

        # --- BULLETPROOF LIVE MAP ---
        t_vals = [i * 0.1 for i in range(64)]
        gx, gy = [500 + 400 * math.cos(i) for i in t_vals], [300 + 150 * math.sin(i) for i in t_vals]
        fig_m = go.Figure(go.Scatter(x=gx, y=gy, mode='lines', line=dict(color='rgba(255,255,255,0.1)', width=2), showlegend=False))
        
        # Bypass Pandas: Extract coordinates directly from the raw dictionary
        if latest_ham.get('Position_X'):
            fig_m.add_trace(go.Scatter(
                x=[float(latest_ham['Position_X'])], 
                y=[float(latest_ham['Position_Y'])],
                mode='markers', name='HAM',
                marker=dict(size=15, color=DRIVER_COLORS["HAM"], line=dict(width=2, color='white'))
            ))

        if latest_bot.get('Position_X'):
            fig_m.add_trace(go.Scatter(
                x=[float(latest_bot['Position_X'])], 
                y=[float(latest_bot['Position_Y'])],
                mode='markers', name='BOT',
                marker=dict(size=15, color=DRIVER_COLORS["BOT"], line=dict(width=2, color='white'))
            ))
        
        fig_m.update_layout(xaxis=dict(range=[50, 950], visible=False), yaxis=dict(range=[100, 500], visible=False),
                            margin=dict(l=0, r=0, t=0, b=0), height=300, showlegend=False, uirevision="constant",
                            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        track_map.plotly_chart(fig_m, use_container_width=True, key=f"m_{loop_count}")

        # --- HEATMAPS ---
        h_loss = int(float(latest_ham.get('TractionLoss', 0))) == 1
        b_loss = int(float(latest_bot.get('TractionLoss', 0))) == 1
        tire_ham.plotly_chart(draw_car_heatmap("HAM", h_loss), use_container_width=True, key=f"h1_{loop_count}")
        tire_bot.plotly_chart(draw_car_heatmap("BOT", b_loss), use_container_width=True, key=f"h2_{loop_count}")
        
        # --- CHARTS ---
        if not df.empty:
            speed_chart.plotly_chart(format_line_chart(px.line(df, x='Timestamp', y='Speed', color='Driver', color_discrete_map=DRIVER_COLORS, category_orders=DRIVER_ORDER), df), use_container_width=True, key=f"s_{loop_count}")
            rpm_chart.plotly_chart(format_line_chart(px.line(df, x='Timestamp', y='RPM', color='Driver', color_discrete_map=DRIVER_COLORS, category_orders=DRIVER_ORDER), df), use_container_width=True, key=f"r_{loop_count}")
            throttle_chart.plotly_chart(format_line_chart(px.line(df, x='Timestamp', y='Throttle', color='Driver', color_discrete_map=DRIVER_COLORS, category_orders=DRIVER_ORDER), df), use_container_width=True, key=f"t_{loop_count}")
        
    time.sleep(1)