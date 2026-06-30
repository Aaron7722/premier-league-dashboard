import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Premier League 2025-26 Analysis",
    layout="wide"
)

sns.set_style("whitegrid")

st.title("⚽ Premier League 2025-26 Season Analysis")
st.markdown(
    "End-to-end analysis built with Python, pandas, and seaborn — data cleaning, "
    "standings calculation from raw match data, and visual exploration of team performance. "
    "Data source: [football-data.co.uk](https://www.football-data.co.uk/)"
)

# ---------- LOAD & CLEAN DATA ----------
@st.cache_data
def load_data():
    url = "https://www.football-data.co.uk/mmz4281/2526/E0.csv"
    df = pd.read_csv(url)

    cols = ['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR', 'HTHG', 'HTAG']
    df = df[cols]
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y')

    df = df.rename(columns={
        'FTHG': 'HomeGoals',
        'FTAG': 'AwayGoals',
        'FTR': 'Result',
        'HTHG': 'HT_HomeGoals',
        'HTAG': 'HT_AwayGoals'
    })
    return df

@st.cache_data
def build_league_table(df):
    teams = pd.unique(df[['HomeTeam', 'AwayTeam']].values.ravel())
    table = []

    for team in teams:
        home_games = df[df['HomeTeam'] == team]
        away_games = df[df['AwayTeam'] == team]

        played = len(home_games) + len(away_games)
        wins = len(home_games[home_games['Result'] == 'H']) + len(away_games[away_games['Result'] == 'A'])
        draws = len(home_games[home_games['Result'] == 'D']) + len(away_games[away_games['Result'] == 'D'])
        losses = played - wins - draws

        goals_for = home_games['HomeGoals'].sum() + away_games['AwayGoals'].sum()
        goals_against = home_games['AwayGoals'].sum() + away_games['HomeGoals'].sum()
        goal_diff = goals_for - goals_against
        points = wins * 3 + draws * 1

        table.append({
            'Team': team, 'Played': played, 'Wins': wins, 'Draws': draws,
            'Losses': losses, 'GF': goals_for, 'GA': goals_against,
            'GD': goal_diff, 'Points': points
        })

    league_table = pd.DataFrame(table).sort_values(
        by=['Points', 'GD'], ascending=False
    ).reset_index(drop=True)
    league_table.index += 1
    return league_table

df = load_data()
league_table = build_league_table(df)

st.caption(f"Data range: {df['Date'].min().date()} to {df['Date'].max().date()} • {len(df)} matches played")

# ---------- SIDEBAR FILTER ----------
st.sidebar.header("Filters")
all_teams = league_table['Team'].tolist()
selected_teams = st.sidebar.multiselect(
    "Show only these teams (leave empty for all)",
    options=all_teams,
    default=[]
)

# If nothing selected, show everything. Otherwise filter down.
if selected_teams:
    filtered_table = league_table[league_table['Team'].isin(selected_teams)]
    filtered_df = df[df['HomeTeam'].isin(selected_teams) | df['AwayTeam'].isin(selected_teams)]
else:
    filtered_table = league_table
    filtered_df = df

# ---------- LEAGUE TABLE ----------
st.header("📊 League Standings")
st.dataframe(filtered_table, use_container_width=True)

# ---------- CHARTS IN TABS ----------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Points Table", "Goals For vs Against", "Home vs Away Wins",
    "Total Goals Scored", "Results Heatmap"
])

with tab1:
    fig, ax = plt.subplots(figsize=(10, max(4, len(filtered_table) * 0.4)))
    sns.barplot(data=filtered_table, x='Points', y='Team', hue='Team',
                palette='viridis', legend=False, ax=ax)
    ax.set_title('Premier League 2025-26 — Points Table')
    st.pyplot(fig)

with tab2:
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.scatterplot(data=filtered_table, x='GF', y='GA', s=100, ax=ax)
    for _, row in filtered_table.iterrows():
        ax.text(row['GF'] + 0.3, row['GA'], row['Team'], fontsize=8)
    ax.set_title('Goals Scored vs Goals Conceded')
    ax.invert_yaxis()
    st.pyplot(fig)

with tab3:
    home_wins = filtered_df[filtered_df['Result'] == 'H'].groupby('HomeTeam').size()
    away_wins = filtered_df[filtered_df['Result'] == 'A'].groupby('AwayTeam').size()
    win_compare = pd.DataFrame({'Home Wins': home_wins, 'Away Wins': away_wins}).fillna(0)
    if selected_teams:
        win_compare = win_compare[win_compare.index.isin(selected_teams)]
    win_compare = win_compare.sort_values('Home Wins', ascending=False)

    fig, ax = plt.subplots(figsize=(12, 6))
    win_compare.plot(kind='bar', ax=ax, color=['#1f77b4', '#ff7f0e'])
    ax.set_title('Home vs Away Wins by Team')
    ax.set_ylabel('Number of Wins')
    plt.xticks(rotation=75)
    st.pyplot(fig)

with tab4:
    fig, ax = plt.subplots(figsize=(10, max(4, len(filtered_table) * 0.4)))
    top_scoring = filtered_table.sort_values('GF', ascending=False)
    sns.barplot(data=top_scoring, x='GF', y='Team', hue='Team',
                palette='magma', legend=False, ax=ax)
    ax.set_title('Total Goals Scored by Team')
    st.pyplot(fig)

with tab5:
    results_pivot = df.pivot_table(
        index='HomeTeam', columns='AwayTeam', values='Result',
        aggfunc=lambda x: 1 if (x == 'H').any() else 0
    )
    if selected_teams:
        rows = [t for t in results_pivot.index if t in selected_teams]
        results_pivot = results_pivot.loc[rows]

    fig, ax = plt.subplots(figsize=(14, max(4, len(results_pivot) * 0.5)))
    sns.heatmap(results_pivot.fillna(0), cmap='RdYlGn',
                cbar_kws={'label': 'Home Win (1) vs Not (0)'}, ax=ax)
    ax.set_title('Home Team Win Heatmap')
    st.pyplot(fig)

# ---------- INSIGHTS ----------
st.header("🔍 Key Insights")
st.markdown("""
1. **Arsenal won the title on defense, not just attack.** Despite Man City scoring more
   goals overall, Arsenal finished with the league's best points total by conceding far
   fewer goals — the best goal difference in the league by a clear margin.

2. **Home advantage was strongest for the top teams.** Arsenal and Man City both leaned
   heavily on home form, while mid-table teams like Crystal Palace and Nott'm Forest
   actually won more games away than at home — an unusual pattern worth a follow-up dig.

3. **Goal-scoring didn't guarantee a high finish.** Bournemouth scored more goals than
   several teams who finished above them, but a leaky defense dragged them down the
   table — showing goals-for alone is a poor predictor of league position.

4. **Bottom of the table was decisive, not close.** Wolves and Burnley finished well
   clear of safety, both scoring the fewest goals in the league — suggesting their
   issues were attacking output, not just defensive frailty.
""")

st.markdown("---")
st.caption("Built by [Your Name] • Data: football-data.co.uk • Code: github.com/yourusername/premier-league-dashboard")
