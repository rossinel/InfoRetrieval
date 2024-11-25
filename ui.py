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
                ),

                # Sort options
                html.Div(
                    children=[
                        html.Label("Sort By:", style={'marginRight': '10px'}),
                        dcc.Dropdown(
                            id='sort-by',
                            options=[
                                {'label': 'Title', 'value': 'episode_title'},
                                {'label': 'Release Date', 'value': 'air_date'},
                                {'label': 'Rating', 'value': 'rating'},
                            ],
                            placeholder="Select sorting criteria",
                            style={'width': '200px', 'marginRight': '20px'}
                        ),
                        dcc.RadioItems(
                            id='sort-order',
                            options=[
                                {'label': 'Ascending', 'value': 'ASC'},
                                {'label': 'Descending', 'value': 'DESC'}
                            ],
                            value='ASC',
                            style={'display': 'inline-block'}
                        )
                    ],
                    style={'display': 'flex', 'alignItems': 'center', 'marginTop': '10px'}
                ),

                # Apply filters button
                html.Button("Apply Filters", id='apply-filters', n_clicks=0, style={
                    'marginTop': '10px', 'backgroundColor': '#3498db', 'color': 'white', 'border': 'none', 'padding': '10px 20px', 'cursor': 'pointer'
                })
            ]
        ),

        # Results table
        html.Div(
            children=[
                dash_table.DataTable(
                    id='results-table',
                    columns=[
                        {"name": "Show", "id": "show"},
                        {"name": "Season", "id": "season"},
                        {"name": "Episode", "id": "episode"},
                        {"name": "Title", "id": "episode_title"},
                        {"name": "Air Date", "id": "air_date"},
                        {"name": "Rating", "id": "rating"},
                        {"name": "Votes", "id": "votes"},
                        {"name": "Plot", "id": "plot"},
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
                )
            ]
        )
    ]
)

# Callbacks
@app.callback(
    Output('results-table', 'data'),
    Input('apply-filters', 'n_clicks'),
    State('search-title', 'value'),
    State('filter-show', 'value'),
    State('filter-date', 'start_date'),
    State('filter-date', 'end_date'),
    State('filter-rating', 'value'),
    State('sort-by', 'value'),
    State('sort-order', 'value')
)
def update_table(n_clicks, search_title, filter_show, start_date, end_date, filter_rating, sort_by, sort_order):
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
    
    # Apply sorting
    if sort_by:
        df = df.sort_values(by=sort_by, ascending=(sort_order == 'ASC'))
        
    df['episode_title'] = df['episode_title'].str.split('∙').str[-1]

    return df.to_dict('records')

# Run app
if __name__ == '__main__':
    app.run_server(debug=True)
