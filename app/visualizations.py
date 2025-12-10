"""
All visualization functions untuk IoT Hydroponics Dashboard
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from config import STATUS_COLORS

def create_temperature_trend_chart(df_log):
    """Create temperature trend chart (air & water temperature)"""
    if df_log.empty or len(df_log) < 2:
        return None

    df_recent = df_log.tail(30).copy()
    df_recent['timestamp'] = pd.to_datetime(df_recent['timestamp'])

    fig = make_subplots(specs=[[{"secondary_y": False}]])

    # Air Temperature
    fig.add_trace(
        go.Scatter(
            x=df_recent['timestamp'],
            y=df_recent['air_temperature'],
            mode='lines+markers',
            name='Air Temp',
            line=dict(color='#ff7f0e', width=2),
            marker=dict(size=6)
        )
    )

    # Water Temperature
    fig.add_trace(
        go.Scatter(
            x=df_recent['timestamp'],
            y=df_recent['water_temperature'],
            mode='lines+markers',
            name='Water Temp',
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=6)
        )
    )

    fig.update_layout(
        title="Temperature Trends (Last 30 readings)",
        xaxis_title="Time",
        yaxis_title="Temperature (°C)",
        height=400,
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig

def create_ph_tds_chart(df_log):
    """Create pH and TDS trend chart"""
    if df_log.empty or len(df_log) < 2:
        return None

    df_recent = df_log.tail(30).copy()
    df_recent['timestamp'] = pd.to_datetime(df_recent['timestamp'])

    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("pH Level", "TDS Level (ppm)"),
        vertical_spacing=0.15
    )

    # pH Chart
    fig.add_trace(
        go.Scatter(
            x=df_recent['timestamp'],
            y=df_recent['ph'],
            mode='lines+markers',
            name='pH',
            line=dict(color='#2ca02c', width=2),
            marker=dict(size=6),
            fill='tozeroy',
            fillcolor='rgba(44, 160, 44, 0.1)'
        ),
        row=1, col=1
    )

    # TDS Chart
    fig.add_trace(
        go.Scatter(
            x=df_recent['timestamp'],
            y=df_recent['tds'],
            mode='lines+markers',
            name='TDS',
            line=dict(color='#d62728', width=2),
            marker=dict(size=6),
            fill='tozeroy',
            fillcolor='rgba(214, 39, 40, 0.1)'
        ),
        row=2, col=1
    )

    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_yaxes(title_text="pH", row=1, col=1)
    fig.update_yaxes(title_text="ppm", row=2, col=1)

    fig.update_layout(
        height=500,
        showlegend=False,
        hovermode='x unified'
    )

    return fig

def create_humidity_chart(df_log):
    """Create humidity trend chart"""
    if df_log.empty or len(df_log) < 2:
        return None

    df_recent = df_log.tail(30).copy()
    df_recent['timestamp'] = pd.to_datetime(df_recent['timestamp'])

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df_recent['timestamp'],
            y=df_recent['air_humidity'],
            mode='lines+markers',
            name='Humidity',
            line=dict(color='#9467bd', width=2),
            marker=dict(size=6),
            fill='tozeroy',
            fillcolor='rgba(148, 103, 189, 0.2)'
        )
    )

    fig.update_layout(
        title="Air Humidity Trend",
        xaxis_title="Time",
        yaxis_title="Humidity (%)",
        height=350,
        showlegend=False
    )

    return fig

def create_light_chart(df_log):
    """Create light (LDR) trend chart"""
    if df_log.empty or len(df_log) < 2:
        return None

    df_recent = df_log.tail(30).copy()
    df_recent['timestamp'] = pd.to_datetime(df_recent['timestamp'])

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df_recent['timestamp'],
            y=df_recent['ldr_value'],
            mode='lines+markers',
            name='Light',
            line=dict(color='#ffbb00', width=2),
            marker=dict(size=6),
            fill='tozeroy',
            fillcolor='rgba(255, 187, 0, 0.2)'
        )
    )

    fig.update_layout(
        title="Light Intensity Trend (LDR)",
        xaxis_title="Time",
        yaxis_title="LDR Value",
        height=350,
        showlegend=False
    )

    return fig

def create_water_level_chart(df_log):
    """Create water level and flow trend chart"""
    if df_log.empty or len(df_log) < 2:
        return None

    df_recent = df_log.tail(30).copy()
    df_recent['timestamp'] = pd.to_datetime(df_recent['timestamp'])

    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("Water Level (cm)", "Water Flow"),
        vertical_spacing=0.15
    )

    # Water Level
    fig.add_trace(
        go.Scatter(
            x=df_recent['timestamp'],
            y=df_recent['water_level'],
            mode='lines+markers',
            name='Water Level',
            line=dict(color='#17becf', width=2),
            marker=dict(size=6),
            fill='tozeroy',
            fillcolor='rgba(23, 190, 207, 0.2)'
        ),
        row=1, col=1
    )

    # Water Flow
    fig.add_trace(
        go.Scatter(
            x=df_recent['timestamp'],
            y=df_recent['water_flow'],
            mode='lines+markers',
            name='Water Flow',
            line=dict(color='#8c564b', width=2),
            marker=dict(size=6),
            fill='tozeroy',
            fillcolor='rgba(140, 86, 75, 0.2)'
        ),
        row=2, col=1
    )

    fig.update_xaxes(title_text="Time", row=2, col=1)
    fig.update_yaxes(title_text="cm", row=1, col=1)
    fig.update_yaxes(title_text="Flow", row=2, col=1)

    fig.update_layout(
        height=500,
        showlegend=False,
        hovermode='x unified'
    )

    return fig

def create_status_pie_chart(df_log):
    """Create status distribution pie chart"""
    if df_log.empty:
        return None

    if 'status' not in df_log.columns:
        return None
        
    counts = df_log['status'].value_counts()
    
    fig = px.pie(
        values=counts.values,
        names=counts.index,
        title="Status Distribution",
        color=counts.index,
        color_discrete_map=STATUS_COLORS
    )
    fig.update_traces(textinfo='percent+label+value')
    fig.update_layout(height=400)
    return fig

def create_label_distribution_charts(df_log):
    """Create distribution charts for all 4 labels"""
    if df_log.empty:
        return None

    # Check if label columns exist
    label_cols = ['ph_label', 'tds_label', 'ambient_label', 'light_label']
    if not all(col in df_log.columns for col in label_cols):
        return None

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("pH Labels", "TDS Labels", "Ambient Labels", "Light Labels"),
        specs=[[{"type": "pie"}, {"type": "pie"}],
               [{"type": "pie"}, {"type": "pie"}]]
    )

    # pH Labels
    ph_counts = df_log['ph_label'].value_counts()
    fig.add_trace(
        go.Pie(labels=ph_counts.index, values=ph_counts.values, name="pH"),
        row=1, col=1
    )

    # TDS Labels
    tds_counts = df_log['tds_label'].value_counts()
    fig.add_trace(
        go.Pie(labels=tds_counts.index, values=tds_counts.values, name="TDS"),
        row=1, col=2
    )

    # Ambient Labels
    ambient_counts = df_log['ambient_label'].value_counts()
    fig.add_trace(
        go.Pie(labels=ambient_counts.index, values=ambient_counts.values, name="Ambient"),
        row=2, col=1
    )

    # Light Labels
    light_counts = df_log['light_label'].value_counts()
    fig.add_trace(
        go.Pie(labels=light_counts.index, values=light_counts.values, name="Light"),
        row=2, col=2
    )

    fig.update_traces(textinfo='percent+label')
    fig.update_layout(height=600, showlegend=False)
    return fig

def create_correlation_heatmap(df_log):
    """Create correlation heatmap for sensor values"""
    if df_log.empty or len(df_log) < 2:
        return None

    # Select numeric sensor columns
    sensor_cols = ['ph', 'tds', 'water_temperature', 'air_temperature', 
                   'air_humidity', 'ldr_value', 'water_flow', 'water_level']
    
    available_cols = [col for col in sensor_cols if col in df_log.columns]
    
    if len(available_cols) < 2:
        return None

    corr_matrix = df_log[available_cols].corr()

    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.columns,
        colorscale='RdBu',
        zmid=0,
        text=corr_matrix.values,
        texttemplate='%{text:.2f}',
        textfont={"size": 10},
        colorbar=dict(title="Correlation")
    ))

    fig.update_layout(
        title="Sensor Data Correlation Matrix",
        height=500,
        xaxis={'side': 'bottom'}
    )

    return fig