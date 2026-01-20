"""
Dash dashboard for real-time social media analytics visualization
"""
from datetime import datetime, timedelta
from typing import Dict, List, Any

import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd

from src.config import config
from src.storage.elasticsearch_client import ElasticsearchClient
from src.storage.clickhouse_client import ClickHouseClient


# Initialize clients
es_client = ElasticsearchClient()
ch_client = ClickHouseClient()

# Create Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
    title="Social Media Analytics Dashboard"
)

# Layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("📊 Social Media Analytics Dashboard", className="text-center mb-4"),
            html.Hr()
        ])
    ]),
    
    # Controls
    dbc.Row([
        dbc.Col([
            dbc.Label("Time Range:"),
            dcc.Dropdown(
                id='time-range',
                options=[
                    {'label': 'Last Hour', 'value': '1h'},
                    {'label': 'Last 6 Hours', 'value': '6h'},
                    {'label': 'Last 24 Hours', 'value': '24h'},
                    {'label': 'Last 7 Days', 'value': '7d'},
                    {'label': 'Last 30 Days', 'value': '30d'},
                ],
                value='24h'
            )
        ], width=3),
        dbc.Col([
            dbc.Label("Platform:"),
            dcc.Dropdown(
                id='platform-filter',
                options=[
                    {'label': 'All Platforms', 'value': 'all'},
                    {'label': 'Twitter/X', 'value': 'x'},
                    {'label': 'Threads', 'value': 'threads'},
                    {'label': 'Reddit', 'value': 'reddit'},
                ],
                value='all'
            )
        ], width=3),
        dbc.Col([
            dbc.Button(
                "🔄 Refresh",
                id="refresh-button",
                color="primary",
                className="mt-4"
            )
        ], width=2)
    ], className="mb-4"),
    
    # Stats cards
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("📝 Total Posts", className="card-title"),
                    html.H2(id="total-posts", className="text-primary")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("👥 Unique Users", className="card-title"),
                    html.H2(id="unique-users", className="text-success")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("❤️ Total Likes", className="card-title"),
                    html.H2(id="total-likes", className="text-danger")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("📈 Avg Engagement", className="card-title"),
                    html.H2(id="avg-engagement", className="text-info")
                ])
            ])
        ], width=3),
    ], className="mb-4"),
    
    # Time series chart
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📈 Activity Over Time"),
                dbc.CardBody([
                    dcc.Graph(id="timeseries-chart")
                ])
            ])
        ])
    ], className="mb-4"),
    
    # Platform distribution and engagement
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🌐 Platform Distribution"),
                dbc.CardBody([
                    dcc.Graph(id="platform-pie-chart")
                ])
            ])
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("⚡ Engagement by Platform"),
                dbc.CardBody([
                    dcc.Graph(id="engagement-bar-chart")
                ])
            ])
        ], width=6),
    ], className="mb-4"),
    
    # Trending keywords
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🔥 Trending Keywords"),
                dbc.CardBody([
                    dcc.Graph(id="trending-keywords-chart")
                ])
            ])
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("👤 Top Users"),
                dbc.CardBody([
                    html.Div(id="top-users-list")
                ])
            ])
        ], width=6),
    ], className="mb-4"),
    
    # Viral posts
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🔥 Viral Posts"),
                dbc.CardBody([
                    html.Div(id="viral-posts-list")
                ])
            ])
        ])
    ], className="mb-4"),
    
    # Auto-refresh interval
    dcc.Interval(
        id='interval-component',
        interval=60*1000,  # 60 seconds
        n_intervals=0
    )
], fluid=True)


def get_time_range(value: str) -> tuple:
    """Convert time range value to datetime range"""
    end_date = datetime.now()
    
    if value == '1h':
        start_date = end_date - timedelta(hours=1)
    elif value == '6h':
        start_date = end_date - timedelta(hours=6)
    elif value == '24h':
        start_date = end_date - timedelta(hours=24)
    elif value == '7d':
        start_date = end_date - timedelta(days=7)
    elif value == '30d':
        start_date = end_date - timedelta(days=30)
    else:
        start_date = end_date - timedelta(hours=24)
    
    return start_date, end_date


@app.callback(
    [
        Output('total-posts', 'children'),
        Output('unique-users', 'children'),
        Output('total-likes', 'children'),
        Output('avg-engagement', 'children'),
    ],
    [
        Input('refresh-button', 'n_clicks'),
        Input('interval-component', 'n_intervals'),
    ],
    [
        State('time-range', 'value'),
        State('platform-filter', 'value')
    ]
)
def update_stats(n_clicks, n_intervals, time_range, platform):
    """Update statistics cards"""
    start_date, end_date = get_time_range(time_range)
    
    try:
        stats = ch_client.get_statistics(start_date, end_date)
        
        return (
            f"{stats['total_posts']:,}",
            f"{stats['unique_users']:,}",
            f"{stats['total_likes']:,}",
            f"{stats['avg_engagement']:.2f}"
        )
    except Exception as e:
        return "N/A", "N/A", "N/A", "N/A"


@app.callback(
    Output('timeseries-chart', 'figure'),
    [
        Input('refresh-button', 'n_clicks'),
        Input('interval-component', 'n_intervals'),
    ],
    [
        State('time-range', 'value'),
        State('platform-filter', 'value')
    ]
)
def update_timeseries(n_clicks, n_intervals, time_range, platform):
    """Update time series chart"""
    start_date, end_date = get_time_range(time_range)
    
    try:
        platform_filter = None if platform == 'all' else platform
        df = ch_client.query_time_series(
            start_date=start_date,
            end_date=end_date,
            platform=platform_filter,
            interval='1 HOUR'
        )
        
        fig = px.line(
            df,
            x='time_bucket',
            y='post_count',
            color='platform',
            title='Posts Over Time',
            labels={'time_bucket': 'Time', 'post_count': 'Number of Posts'}
        )
        
        fig.update_layout(
            hovermode='x unified',
            template='plotly_white'
        )
        
        return fig
    except Exception as e:
        return go.Figure()


@app.callback(
    Output('platform-pie-chart', 'figure'),
    [
        Input('refresh-button', 'n_clicks'),
        Input('interval-component', 'n_intervals'),
    ],
    [State('time-range', 'value')]
)
def update_platform_distribution(n_clicks, n_intervals, time_range):
    """Update platform distribution pie chart"""
    start_date, end_date = get_time_range(time_range)
    
    try:
        df = ch_client.query_time_series(start_date, end_date, interval='1 DAY')
        platform_counts = df.groupby('platform')['post_count'].sum()
        
        fig = px.pie(
            values=platform_counts.values,
            names=platform_counts.index,
            title='Posts by Platform'
        )
        
        return fig
    except Exception as e:
        return go.Figure()


@app.callback(
    Output('engagement-bar-chart', 'figure'),
    [
        Input('refresh-button', 'n_clicks'),
        Input('interval-component', 'n_intervals'),
    ],
    [State('time-range', 'value')]
)
def update_engagement_chart(n_clicks, n_intervals, time_range):
    """Update engagement bar chart"""
    start_date, end_date = get_time_range(time_range)
    
    try:
        df = ch_client.query_time_series(start_date, end_date, interval='1 DAY')
        platform_engagement = df.groupby('platform').agg({
            'total_likes': 'sum',
            'total_shares': 'sum',
            'total_comments': 'sum'
        })
        
        fig = go.Figure(data=[
            go.Bar(name='Likes', x=platform_engagement.index, y=platform_engagement['total_likes']),
            go.Bar(name='Shares', x=platform_engagement.index, y=platform_engagement['total_shares']),
            go.Bar(name='Comments', x=platform_engagement.index, y=platform_engagement['total_comments'])
        ])
        
        fig.update_layout(
            barmode='group',
            title='Engagement Metrics by Platform',
            template='plotly_white'
        )
        
        return fig
    except Exception as e:
        return go.Figure()


@app.callback(
    Output('trending-keywords-chart', 'figure'),
    [
        Input('refresh-button', 'n_clicks'),
        Input('interval-component', 'n_intervals'),
    ],
    [State('time-range', 'value')]
)
def update_trending_keywords(n_clicks, n_intervals, time_range):
    """Update trending keywords chart"""
    start_date, end_date = get_time_range(time_range)
    
    try:
        tags = ch_client.get_trending_tags(start_date, end_date, limit=20)
        
        df = pd.DataFrame(tags)
        
        fig = px.bar(
            df,
            x='frequency',
            y='tag',
            orientation='h',
            title='Top 20 Trending Keywords'
        )
        
        fig.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            template='plotly_white'
        )
        
        return fig
    except Exception as e:
        return go.Figure()


@app.callback(
    Output('top-users-list', 'children'),
    [
        Input('refresh-button', 'n_clicks'),
        Input('interval-component', 'n_intervals'),
    ],
    [State('time-range', 'value')]
)
def update_top_users(n_clicks, n_intervals, time_range):
    """Update top users list"""
    start_date, end_date = get_time_range(time_range)
    
    try:
        df = ch_client.get_top_users(start_date, end_date, limit=10)
        
        items = []
        for idx, row in df.iterrows():
            items.append(
                dbc.ListGroupItem([
                    html.H6(f"{row['user_name']} ({row['platform']})"),
                    html.Small(f"Posts: {row['post_count']} | Engagement: {row['total_engagement']:.0f}")
                ])
            )
        
        return dbc.ListGroup(items)
    except Exception as e:
        return html.P("No data available")


@app.callback(
    Output('viral-posts-list', 'children'),
    [
        Input('refresh-button', 'n_clicks'),
        Input('interval-component', 'n_intervals'),
    ],
    [State('time-range', 'value')]
)
def update_viral_posts(n_clicks, n_intervals, time_range):
    """Update viral posts list"""
    start_date, end_date = get_time_range(time_range)
    
    try:
        viral_posts = es_client.get_viral_posts(threshold=5000, start_date=start_date, size=5)
        
        items = []
        for post in viral_posts[:5]:
            items.append(
                dbc.Card([
                    dbc.CardBody([
                        html.H6(post.get('title') or post.get('content', '')[:100]),
                        html.P([
                            f"👤 {post.get('user_name', 'Unknown')} | ",
                            f"❤️ {post.get('num_likes', 0):,} | ",
                            f"🔄 {post.get('num_shares', 0):,} | ",
                            f"💬 {post.get('num_comments', 0):,}"
                        ], className="mb-0 text-muted small")
                    ])
                ], className="mb-2")
            )
        
        return items if items else html.P("No viral posts found")
    except Exception as e:
        return html.P("No data available")


def run_dashboard(host: str = "0.0.0.0", port: int = 8050):
    """Run the dashboard"""
    app.run_server(host=host, port=port, debug=True)


if __name__ == "__main__":
    run_dashboard()
