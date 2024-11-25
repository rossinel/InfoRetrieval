import dash
from dash import dcc, html, Input, Output, State, dash_table
import sqlite3
import pandas as pd

# Initialize Dash app
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
                                # Add other shows here if available
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

        # Results table
        html.Div(
            children=[
                dash_table.DataTable(
                    id='results-table',
                    columns=[
                        {"name": "Show", "id": "show"},
                        {"name": "Title", "id": "episode_title"},
                        {"name": "Rating", "id": "rating"},
                        {"name": "Votes", "id": "votes"},
                        {"name": "Plot", "id": "plot"},
                        {"name": "Air Date", "id": "air_date"},
                        {"name": "Season", "id": "season"},
                        {"name": "Episode", "id": "episode"},
                    ],
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'left',
                        'padding': '10px',
                        'whiteSpace': 'normal'
                    },
                    style_header={
                        'backgroundColor': '#2c3e50',
                        'color': 'white',
                        'fontWeight': 'bold'
                    },
                    style_data={'backgroundColor': '#ecf0f1', 'color': '#2c3e50'},
                    page_size=20,
                    sort_action="native",  # Enable native sorting by clicking column headers
                )
            ]
        )
    ]
)

# Callbacks
@app.callback(
    Output('results-table', 'data'),
    Input('search-title', 'value'),
    Input('filter-show', 'value'),
    Input('filter-date', 'start_date'),
    Input('filter-date', 'end_date'),
    Input('filter-rating', 'value')
)
def update_table(search_title, filter_show, start_date, end_date, filter_rating):
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
    
    df['episode_title'] = df['episode_title'].str.split('∙').str[-1]
    
    # votes column is ithere 4.7 or 4700, if there are no . devide by 1000, and to both add K
    df['votes'] = df['votes'].apply(lambda x: f"{x/1000}K" if ".0" in str(x) else f"{x}K")
    
    # from "Tue, Sep 28, 1999" to" 1999-09-28"
    df['air_date'] = pd.to_datetime(df['air_date'], format='%a, %b %d, %Y').dt.strftime('%Y-%m-%d')

    return df.to_dict('records')

# Run app
if __name__ == '__main__':
    app.run_server(debug=True)
