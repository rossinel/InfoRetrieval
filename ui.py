import dash
from dash import dcc, html, Input, Output, State
import sqlite3
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = dash.Dash(__name__)
app.title = "Episode Browser"


# =========================
# Helper Functions
# =========================

# the main function used to fetch data from the database
def fetch_data_from_db(filters=None, params=None):
    conn = sqlite3.connect("episodes.db")
    query = "SELECT * FROM episodes"
    if filters:
        query += f" WHERE {filters}"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

# this function will format the votes to be more readable
def format_votes(vote):
    try:
        if isinstance(vote, float) and vote >= 1000:
            return f"{int(vote // 1000)}K"
        elif isinstance(vote, float) and vote <= 100:
            return f"{int(vote)}K"
        else:
            return int(vote)
    except Exception:
        return vote


# this function will find similar plots based on the input plot and show name
def find_similar_plots(database_path="episodes.db", input_plot='', show_name='', plot_id=None, top_n=3):
    conn = sqlite3.connect(database_path)

    query = """
        SELECT * FROM episodes
        WHERE show = ?
    """
    plots_df = pd.read_sql_query(query, conn, params=(show_name,))
    conn.close()

    all_plots = plots_df['plot'].tolist()
    all_plots.insert(0, input_plot)  # Add input plot to the beginning

    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(all_plots)

    similarity_scores = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

    plots_df['similarity'] = similarity_scores

    if plot_id:
        plots_df = plots_df[plots_df['id'] != plot_id]
    most_similar_plots = plots_df.sort_values(by='similarity', ascending=False).head(top_n)

    return most_similar_plots


def create_similar_episodes_section(similar_df):
    suggestions = []
    for _, sim_row in similar_df.iterrows():
        suggestions.append(
            html.Div(
                children=[
                    html.P(
                        sim_row['episode_title'],
                        style={
                            'color': '#2c3e50',
                            'margin': '5px 0',
                            'fontWeight': 'bold',
                            'fontSize': '14px'
                        }
                    ),
                    html.P(
                        f"Air Date: {sim_row['air_date']}",
                        style={
                            'color': '#7f8c8d',
                            'margin': '0 0 10px 0',
                            'fontSize': '12px'
                        }
                    ),
                ],
                style={'marginBottom': '10px'}
            )
        )
    return suggestions


def create_episode_card(row):
    # Fetch similar episodes
    similar_episodes_df = find_similar_plots(input_plot=row['plot'], show_name=row['show'], plot_id=row['id'])
    suggestions = create_similar_episodes_section(similar_episodes_df)

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
                                    html.H3(
                                        row['episode_title'],
                                        style={'color': '#2c3e50', 'margin': '0'}
                                    ),
                                    html.P(
                                        f"Show: {row['show']}",
                                        style={'color': '#7f8c8d', 'margin': '5px 0'}
                                    ),
                                    html.P(
                                        f"Air Date: {row['air_date']}",
                                        style={'color': '#7f8c8d', 'margin': '5px 0'}
                                    ),
                                    html.P(
                                        [
                                            html.Span(
                                                "★",
                                                style={'color': 'gold', 'marginRight': '5px', 'fontSize': '16px'}
                                            ),
                                            f"{row['rating']} / 10"
                                        ],
                                        style={'color': '#7f8c8d', 'margin': '5px 0'}
                                    ),
                                    html.P(
                                        f"Votes: {row['votes']}",
                                        style={'color': '#7f8c8d', 'margin': '5px 0'}
                                    ),
                                    html.P(
                                        row['plot'],
                                        style={'color': '#34495e', 'margin': '10px 0'}
                                    ),
                                ]
                            )
                        ]
                    ),
                    # Right column: suggestions
                    html.Div(
                        children=[
                            html.H4("Similar Episodes", style={'color': '#2c3e50', 'margin': '0 0 10px 0'}),
                            *suggestions
                        ],
                        style={'flex': '1', 'marginLeft': '20px'}
                    ),
                ]
            )
        ]
    )
    return card


# =========================
# Layout
# =========================

app.layout = html.Div(
    style={'fontFamily': 'Arial, sans-serif', 'margin': '20px'},
    children=[
        html.H1(
            "Episode Browser",
            style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '30px'}
        ),

        # Search Bar
        html.Div(
            style={
                'display': 'flex',
                'justifyContent': 'center',
                'alignItems': 'center',
                'marginBottom': '20px'
            },
            children=[
                html.Label(
                    "Search:",
                    style={'marginRight': '10px', 'fontSize': '18px'}
                ),
                dcc.Input(
                    id='search-title',
                    type='text',
                    placeholder='Enter keyword...',
                    style={
                        'width': '500px',
                        'fontSize': '16px',
                        'padding': '10px',
                        'border': '2px solid #dcdcdc',
                        'height': '38px',
                        'borderRadius': '5px',
                    }
                ),
            ]
        ),

        # Filters Section
        html.Div(
            style={
                'display': 'flex',
                'alignItems': 'center',
                'flexWrap': 'wrap',
                'justifyContent': 'center',
                'gap': '20px',
                'marginBottom': '20px'
            },
            children=[
                # Filter by Show
                html.Div(
                    style={
                        'display': 'flex',
                        'alignItems': 'center',
                        'gap': '10px'
                    },
                    children=[
                        html.Label("Filter by Show:", style={'fontSize': '16px'}),
                        dcc.Dropdown(
                            id='filter-show',
                            options=[
                                {'label': 'Family Guy', 'value': 'Family Guy'},
                                {'label': 'South Park', 'value': 'South Park'},
                                {'label': 'The Simpsons', 'value': 'The Simpsons'},
                            ],
                            placeholder="Select a show",
                            style={
                                'height': '40px',
                                'lineHeight': '30px',
                                'border': '1px solid #dcdcdc',
                                'borderRadius': '5px',
                                'width': '200px',
                                'fontSize': '16px',
                                'boxSizing': 'border-box',
                                'backgroundColor': '#fff'
                            }
                        ),
                    ]
                ),

                # Filter by Release Date
                html.Div(
                    style={
                        'display': 'flex',
                        'alignItems': 'center',
                        'gap': '10px'
                    },
                    children=[
                        html.Label("Filter by Release Date:", style={'fontSize': '16px'}),
                        dcc.DatePickerRange(
                            id='filter-date',
                            start_date_placeholder_text="Start Date",
                            end_date_placeholder_text="End Date",
                            style={
                                'height': '45px',
                                'border': '1px solid #dcdcdc',
                                'boxSizing': 'border-box',
                                'fontSize': '16px',
                                'backgroundColor': '#fff'
                            }
                        ),
                    ]
                ),

                # Filter by Rating
                html.Div(
                    style={'display': 'flex', 'alignItems': 'center', 'gap': '10px'},
                    children=[
                        html.Label("Min Rating:", style={'fontSize': '16px'}),
                        dcc.Input(
                            id='filter-rating',
                            type='number',
                            placeholder='Min Rating',
                            style={
                                'height': '45px',
                                'border': '1px solid #dcdcdc',
                                'borderRadius': '5px',
                                'padding': '0 10px',
                                'fontSize': '16px',
                                'boxSizing': 'border-box'
                            }
                        ),
                    ]
                ),

                # Filter by Season
                html.Div(
                    style={'display': 'flex', 'alignItems': 'center', 'gap': '10px'},
                    children=[
                        html.Label("Filter by Season:", style={'fontSize': '16px'}),
                        dcc.Input(
                            id='filter-season',
                            type='number',
                            placeholder='Season Number',
                            style={
                                'height': '45px',
                                'border': '1px solid #dcdcdc',
                                'borderRadius': '5px',
                                'padding': '0 10px',
                                'fontSize': '16px',
                                'boxSizing': 'border-box'
                            }
                        ),
                    ]
                ),
            ]
        ),

        # Pagination Buttons
        html.Div(
            style={
                'display': 'flex',
                'alignItems': 'center',
                'marginTop': '20px',
                'justifyContent': 'center',
                'gap': '20px',
                'marginBottom': '20px'
            },
            children=[
                html.Button('Previous', id='prev-page', n_clicks=0),
                html.Span(id='page-number'),
                html.Button('Next', id='next-page', n_clicks=0),
            ]
        ),

        html.Div(id='results-container', style={'display': 'block'}),
        html.Div(id='current-page', style={'display': 'none'})
    ]
)


# =========================
# Callbacks
# =========================

@app.callback(
    Output('current-page', 'children'),
    Input('prev-page', 'n_clicks'),
    Input('next-page', 'n_clicks'),
    Input('search-title', 'value'),
    Input('filter-show', 'value'),
    Input('filter-date', 'start_date'),
    Input('filter-date', 'end_date'),
    Input('filter-rating', 'value'),
    Input('filter-season', 'value'),
    State('current-page', 'children')
)
def update_page_number(prev_clicks, next_clicks, search_title, filter_show, start_date, end_date, filter_rating, filter_season, current_page):
    if current_page is None:
        current_page = 1

    ctx = dash.callback_context
    if not ctx.triggered:
        return current_page
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # if it's a filter, reset to page 1
    if trigger_id in ['search-title', 'filter-show', 'filter-date', 'filter-rating', 'filter-season']:
        return 1

    # if it's a pagination button, update the page number
    current_page = int(current_page)
    if trigger_id == 'prev-page' and current_page > 1:
        current_page -= 1
    elif trigger_id == 'next-page':
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
    Input('current-page', 'children'),
    Input('filter-season', 'value')
)
def update_results(search_title, filter_show, start_date, end_date, filter_rating, current_page, filter_season):
    filters = []
    params = []

    # Build filters based on inputs
    if filter_show:
        filters.append("show = ?")
        params.append(filter_show)

    if start_date and end_date:
        filters.append("air_date BETWEEN ? AND ?")
        params += [start_date, end_date]

    if filter_rating is not None:
        filters.append("rating >= ?")
        params.append(filter_rating)

    if filter_season is not None:
        filters.append("season = ?")
        params.append(filter_season)

    where_clause = " AND ".join(filters) if filters else None

    if not current_page:
        current_page = 1

    # Fetch all relevant data
    df = fetch_data_from_db(where_clause, params)

    if 'votes' in df.columns:
        df['votes'] = df['votes'].apply(format_votes)

    # If a search_title is given, apply TF-IDF search
    if search_title and not df.empty:

        # first we combine title and plot into a single text field for searching
        df['text_for_search'] = df['episode_title'].fillna('') + ' ' + df['plot'].fillna('')

        # then we vectorize all episodes + the query
        all_docs = df['text_for_search'].tolist()
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(all_docs)
        query_vec = vectorizer.transform([search_title])

        # Compute similarity
        similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()
        df['similarity'] = similarities

        # Sort by similarity
        df = df.sort_values('similarity', ascending=False)

    else:
        # if there is no search_title, sort by show, season, episode
        df = df.sort_values(['show', 'season', 'episode'], ascending=[True, True, True])

    # Pagination
    results_per_page = 10
    start_idx = (int(current_page) - 1) * results_per_page
    end_idx = start_idx + results_per_page
    df_page = df.iloc[start_idx:end_idx]

    # Create cards
    cards = [create_episode_card(row) for _, row in df_page.iterrows()]
    return cards


if __name__ == '__main__':
    app.run_server(debug=True)
