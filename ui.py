import dash
from dash import dcc, html, Input, Output, State
import sqlite3
import pandas as pd

app = dash.Dash(__name__)
app.title = "Episode Browser"

# Connect to SQLite database and fetch initial data
def fetch_data_from_db(filters=None, params=None, limit=None, offset=None):
    conn = sqlite3.connect("episodes.db")
    query = "SELECT * FROM episodes"

    if filters:
        query += f" WHERE {filters}"

    if limit is not None:
        query += f" LIMIT {limit}"
        if offset is not None:
            query += f" OFFSET {offset}"

    df = pd.read_sql_query(query, conn, params=params)
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
                        html.Label("Results per page:", style={'marginRight': '10px'}),
                        dcc.Input(
                            id='results-per-page',
                            type='number',
                            value=5,
                            min=1,
                            style={'width': '100px'}
                        ),
                    ],
                    style={'display': 'flex', 'alignItems': 'center', 'marginTop': '10px'}
                ),

                # button to move between pages
                html.Div(
                    children=[
                        html.Button('Previous', id='prev-page', n_clicks=0),
                        html.Span(id='page-number', style={'margin': '0 20px'}),
                        html.Button('Next', id='next-page', n_clicks=0),
                    ],
                    style={'display': 'flex', 'alignItems': 'center', 'marginTop': '20px'}
                )
            ]
        ),

        # Results container
        html.Div(
            id='results-container',
            style={'display': 'block'}
        ),
    ]
)

app.layout.children.append(html.Div(id='current-page', style={'display': 'none'}))

# Callbacks
@app.callback(
    Output('current-page', 'children'),
    Input('prev-page', 'n_clicks'),
    Input('next-page', 'n_clicks'),
    State('current-page', 'children')
)
def update_page_number(prev_clicks, next_clicks, current_page):
    ctx = dash.callback_context

    if not ctx.triggered or current_page is None:
        return 1

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    current_page = int(current_page)

    if button_id == 'prev-page' and current_page > 1:
        current_page -= 1
    elif button_id == 'next-page':
        current_page += 1

    return current_page

@app.callback(
    Output('page-number', 'children'),
    Input('current-page', 'children')
)
def display_page_number(current_page):
    return f"Page {current_page}" if current_page else "Page 1"

@app.callback(
    Output('results-container', 'children'),
    Input('search-title', 'value'),
    Input('filter-show', 'value'),
    Input('filter-date', 'start_date'),
    Input('filter-date', 'end_date'),
    Input('filter-rating', 'value'),
    Input('results-per-page', 'value'),
    Input('current-page', 'children')
)
def update_results(search_title, filter_show, start_date, end_date, filter_rating, results_per_page, current_page):
    filters = []
    params = []

    # Build filters based on inputs
    if search_title:
        filters.append("episode_title LIKE ?")
        params.append(f"%{search_title}%")
    if filter_show:
        filters.append("show = ?")
        params.append(filter_show)
    if start_date and end_date:
        filters.append("air_date BETWEEN ? AND ?")
        params.extend([start_date, end_date])
    if filter_rating:
        filters.append("rating >= ?")
        params.append(filter_rating)

    # Combine filters into a SQL WHERE clause
    where_clause = " AND ".join(filters) if filters else None

    # Calculate LIMIT and OFFSET for pagination
    if results_per_page is None or results_per_page < 1:
        results_per_page = 5  # Default value
    if current_page is None:
        current_page = 1

    limit = results_per_page
    offset = (int(current_page) - 1) * int(results_per_page)

    # Fetch data with filters, limit, and offset
    df = fetch_data_from_db(where_clause, params, limit=limit, offset=offset)

    def format_votes(vote):
        try:
            if isinstance(vote, float) and vote >= 1000:
                return f"{vote // 1000}K"
            elif isinstance(vote, float) and vote <= 100:
                return f"{vote}K"
            else:
                return int(vote)
        except:
            return vote

    # Apply the formatting function to the votes column
    df['votes'] = df['votes'].apply(format_votes)

    cards = []
    for _, row in df.iterrows():
        # Fetch similar episodes (up to 3) from the same show
        conn = sqlite3.connect("episodes.db")
        similar_episodes_query = """
            SELECT * FROM episodes
            WHERE show = ? AND episode_title != ?
            ORDER BY RANDOM()
            LIMIT 3
        """
        params_similar = (row['show'], row['episode_title'])
        similar_episodes_df = pd.read_sql_query(similar_episodes_query, conn, params=params_similar)
        conn.close()

        # Create suggestions list
        suggestions = []
        for _, sim_row in similar_episodes_df.iterrows():
            suggestions.append(
                html.Div(
                    children=[
                        html.P(sim_row['episode_title'], style={
                            'color': '#2c3e50',
                            'margin': '5px 0',
                            'fontWeight': 'bold',
                            'fontSize': '14px'
                        }),
                        html.P(f"Air Date: {sim_row['air_date']}", style={
                            'color': '#7f8c8d',
                            'margin': '0 0 10px 0',
                            'fontSize': '12px'
                        }),
                    ],
                    style={'marginBottom': '10px'}
                )
            )

        # Build the card
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
                        # Left column: main content
                        html.Div(
                            style={'flex': '2', 'display': 'flex', 'alignItems': 'flex-start'},
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
                                        html.H3(row['episode_title'], style={
                                            'color': '#2c3e50',
                                            'margin': '0'
                                        }),
                                        html.P(f"Show: {row['show']}", style={
                                            'color': '#7f8c8d',
                                            'margin': '5px 0'
                                        }),
                                        html.P(f"Air Date: {row['air_date']}", style={
                                            'color': '#7f8c8d',
                                            'margin': '5px 0'
                                        }),
                                        html.P(
                                            [
                                                html.Span("★", style={
                                                    'color': 'gold',
                                                    'marginRight': '5px',
                                                    'fontSize': '16px'
                                                }),
                                                f"{row['rating']} / 10"
                                            ],
                                            style={'color': '#7f8c8d', 'margin': '5px 0'}
                                        ),
                                        html.P(f"Votes: {row['votes']}", style={
                                            'color': '#7f8c8d',
                                            'margin': '5px 0'
                                        }),
                                        html.P(row['plot'], style={
                                            'color': '#34495e',
                                            'margin': '10px 0'
                                        }),
                                    ]
                                )
                            ]
                        ),
                        # Right column: suggestions
                        html.Div(
                            children=[
                                html.H4("Similar Episodes", style={
                                    'color': '#2c3e50',
                                    'margin': '0 0 10px 0'
                                }),
                                *suggestions
                            ],
                            style={'flex': '1', 'marginLeft': '20px'}
                        ),
                    ]
                )
            ]
        )
        cards.append(card)

    return cards

# Run app
if __name__ == '__main__':
    app.run_server(debug=True)
