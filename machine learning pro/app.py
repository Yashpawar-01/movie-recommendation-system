import streamlit as st
import pickle
import pandas as pd
import requests
import time

# TMDB API Key
api_key = "df6c25e1195a78c585461784dda19d63"

st.title("🎬 Movie Recommendation System with Posters")

# Load movie data and similarity matrix
movies_dict = pickle.load(open('movies_dict', 'rb'))
movies = pd.DataFrame(movies_dict)
similarity = pickle.load(open('similarity.pkl', 'rb'))

# Extract year if 'release_date' available
if 'release_date' in movies.columns:
    movies['year'] = movies['release_date'].str[:4]
else:
    movies['year'] = ''

@st.cache_data(show_spinner=False)
def fetch_poster_by_title_year(title, year=None, retries=3, delay=1):
    """
    Fetch poster using title and optional year for better matching with retry logic.
    """
    query = title
    if year:
        query = f"{title} {year}"
    for attempt in range(retries):
        try:
            url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={query}"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            results = data.get('results')
            if results:
                # Try exact title match ignoring case
                for movie in results:
                    if movie['title'].lower() == title.lower():
                        poster_path = movie.get('poster_path')
                        if poster_path:
                            return f"https://image.tmdb.org/t/p/w500{poster_path}"
                        else:
                            return "https://via.placeholder.com/500x750?text=No+Poster"
                # Fallback to first result
                poster_path = results[0].get('poster_path')
                if poster_path:
                    return f"https://image.tmdb.org/t/p/w500{poster_path}"
            return "https://via.placeholder.com/500x750?text=No+Poster"
        except Exception as e:
            print(f"Attempt {attempt+1} failed fetching poster for {title}: {e}")
            time.sleep(delay)
    return "https://via.placeholder.com/500x750?text=Error"

def recommend(movie):
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])

    recommended_movie_names = []
    recommended_movie_posters = []

    for i in distances[1:6]:
        title = movies.iloc[i[0]].title
        year = movies.iloc[i[0]]['year'] if 'year' in movies.columns else None
        recommended_movie_names.append(title)
        poster_url = fetch_poster_by_title_year(title, year)
        recommended_movie_posters.append(poster_url)

    return recommended_movie_names, recommended_movie_posters

selected_movie = st.selectbox("🎥 Select a movie", movies['title'].values)

if st.button("Recommend"):
    names, posters = recommend(selected_movie)
    st.subheader("🍿 Top 5 Recommendations")
    cols = st.columns(5)
    for i in range(5):
        with cols[i]:
            st.image(posters[i], use_container_width=True)
            st.caption(names[i])