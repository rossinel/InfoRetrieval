import dash
from dash import dcc, html, Input, Output, State
import sqlite3
import pandas as pd

app = dash.Dash(__name__)
app.title = "Episode Browser"

# Connect to SQLite database and fetch initial data
def fetch_data_from_db(filters=None):
    conn = sqlite3.connect("episodes.db")
    query = "SELECT * FROM episodes"

    if filters:
        query += f" WHERE {filters}"

    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Layout
app.layout = html.Div(
    style={'fontFamily': 'Arial, sans-serif', 'margin': '20px'},
    children=[
        html.H1("Episode Browser", style={'textAlign': 'center', 'color': '#2c3e50'}),

        html.Div(
            style={'marginBottom': '20px'},
            children=[
                # Search bar
                html.Div(
                    children=[
                        html.Label("Search by Title:", style={'marginRight': '10px'}),
                        dcc.Input(
                            id='search-title',
                            type='text',
                            placeholder='Enter title...',
                            style={'width': '300px', 'marginRight': '20px'}
                        ),
                    ],
                    style={'display': 'flex', 'alignItems': 'center'}
                ),

                # Filters
                html.Div(
                    children=[
                        html.Label("Filter by Show:", style={'marginRight': '10px'}),
                        dcc.Dropdown(
                            id='filter-show',
                            options=[
                                {'label': 'Family Guy', 'value': 'Family Guy'},
                                {'label': 'South Park', 'value': 'South Park'},
                                {'label': 'The Simpsons', 'value': 'The Simpsons'},
                            ],
                            placeholder="Select a show",
                            style={'width': '200px', 'marginRight': '20px'}
                        ),
                        html.Label("Filter by Release Date:", style={'marginRight': '10px'}),
                        dcc.DatePickerRange(
                            id='filter-date',
                            start_date_placeholder_text="Start Date",
                            end_date_placeholder_text="End Date",
                            style={'marginRight': '20px'}
                        ),
                        html.Label("Filter by Rating:", style={'marginRight': '10px'}),
                        dcc.Input(
                            id='filter-rating',
                            type='number',
                            placeholder='Min Rating',
                            style={'width': '100px', 'marginRight': '20px'}
                        ),
                    ],
                    style={'display': 'flex', 'alignItems': 'center', 'marginTop': '10px'}
                )
            ]
        ),

        # Results container
        html.Div(
            id='results-container',
            style={'display': 'block'}
        )
    ]
)

# Callbacks
@app.callback(
    Output('results-container', 'children'),
    Input('search-title', 'value'),
    Input('filter-show', 'value'),
    Input('filter-date', 'start_date'),
    Input('filter-date', 'end_date'),
    Input('filter-rating', 'value')
)
def update_results(search_title, filter_show, start_date, end_date, filter_rating):
    filters = []

    # Build filters based on inputs
    if search_title:
        filters.append(f"episode_title LIKE '%{search_title}%'")
    if filter_show:
        filters.append(f"show = '{filter_show}'")
    if start_date and end_date:
        filters.append(f"air_date BETWEEN '{start_date}' AND '{end_date}'")
    if filter_rating:
        filters.append(f"rating >= {filter_rating}")

    # Combine filters into a SQL WHERE clause
    where_clause = " AND ".join(filters) if filters else None

    # Fetch data with filters
    df = fetch_data_from_db(where_clause)

    # Format columns as needed
    df['air_date'] = pd.to_datetime(df['air_date'], format='%a, %b %d, %Y').dt.strftime('%Y-%m-%d')
    df['votes'] = df['votes'].apply(lambda x: f"{x / 1000:.1f}K" if x >= 1000 else f"{x}")

    cards = []
    for _, row in df.iterrows():
        card = html.Div(
            style={
                'border': '1px solid #dcdcdc',
                'borderRadius': '10px',
                'padding': '15px',
                'backgroundColor': '#ffffff',
                'marginBottom': '20px',
                'display': 'block',
                'width': '100%'
            },
            children=[
                html.Div(
                    style={'display': 'flex', 'alignItems': 'flex-start'},
                    children=[
                        html.Img(
                            src=row['image'] if 'image' in row and row['image'] else "https://via.placeholder.com/100",
                            style={
                                'width': '100px',
                                'height': 'auto',
                                'borderRadius': '10px',
                                'marginRight': '15px'
                            }
                        ),
                        html.Div(
                            children=[
                                html.H3(row['episode_title'], style={'color': '#2c3e50', 'margin': '0'}),
                                html.P(f"Show: {row['show']}", style={'color': '#7f8c8d', 'margin': '5px 0'}),
                                html.P(f"Air Date: {row['air_date']}", style={'color': '#7f8c8d', 'margin': '5px 0'}),
                                html.P(f"Rating: {row['rating']} / 10", style={'color': '#7f8c8d', 'margin': '5px 0'}),
                                html.P(f"Votes: {row['votes']}", style={'color': '#7f8c8d', 'margin': '5px 0'}),
                                html.P(row['plot'], style={'color': '#34495e', 'margin': '10px 0'}),
                            ]
                        )
                    ]
                )
            ]
        )
        cards.append(card)

    return cards


# Run app
if __name__ == '__main__':
    app.run_server(debug=True)
