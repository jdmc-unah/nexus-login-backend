import sys
import json
import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier

def main():
    if hasattr(sys.stdin, 'reconfigure'):
        sys.stdin.reconfigure(encoding='utf-8')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    try:
        # Read JSON input from standard input
        input_data = json.loads(sys.stdin.read())
    except Exception as e:
        print(json.dumps({"error": f"Failed to parse stdin: {str(e)}"}))
        return
    history = input_data.get('history', [])
    candidates = input_data.get('candidates', [])

    # If history is empty, populate with some default mock items so the tree can train
    if not history:
        history = [
            {"id": 1, "genre_ids": [28, 12], "vote_average": 8.5, "cast": ["Robert Downey Jr.", "Chris Evans"], "directors": ["Anthony Russo"]},
            {"id": 2, "genre_ids": [35, 10751], "vote_average": 8.0, "cast": ["Jim Carrey"], "directors": ["Tom Shadyac"]},
            {"id": 3, "genre_ids": [28, 53], "vote_average": 9.0, "cast": ["Christian Bale"], "directors": ["Christopher Nolan"]}
        ]

    # Extract user profile from history
    liked_genres = []
    liked_actors = []
    liked_directors = []
    
    for m in history:
        genre_ids = m.get('genre_ids', [])
        for g in genre_ids:
            liked_genres.append(g)
            
        cast = m.get('cast', [])
        for actor in cast:
            liked_actors.append(actor)
            
        directors = m.get('directors', [])
        for director in directors:
            liked_directors.append(director)

    liked_genres_set = set(liked_genres)
    liked_actors_set = set(liked_actors)
    liked_directors_set = set(liked_directors)

    def extract_features(movie):
        # 1. Genre match count (up to 3 genres checked)
        genre_ids = movie.get('genre_ids', [])
        movie_genres = genre_ids[:3]
        genre_match_count = sum(1 for g in movie_genres if g in liked_genres_set)
        
        # 2. Actor match count (how many of the movie's main actors match the liked ones)
        cast = movie.get('cast', [])
        actor_match_count = sum(1 for a in cast if a in liked_actors_set)
        
        # 3. Director match (1 if director is in liked directors, 0 otherwise)
        directors = movie.get('directors', [])
        director_match = 1 if any(d in liked_directors_set for d in directors) else 0
        
        # 4. Rating
        vote_average = float(movie.get('vote_average', 0.0) or 0.0)
        
        return {
            'genre_match_count': genre_match_count,
            'actor_match_count': actor_match_count,
            'director_match': director_match,
            'vote_average': vote_average
        }
    train_features = []
    
    # Process positive history
    for m in history:
        feats = extract_features(m)
        feats['liked'] = 1
        train_features.append(feats)
        
    # Generate synthetic negative examples (liked = 0)
    # 1. Typical movies that do not match the user's preferred genres, actors or directors
    for _ in range(10):
        train_features.append({
            'genre_match_count': 0,
            'actor_match_count': 0,
            'director_match': 0,
            'vote_average': 5.5,
            'liked': 0
        })
        
    # 2. High-rated movies but with absolutely zero matching preferences (teaches tree that rating alone != liked)
    for _ in range(5):
        train_features.append({
            'genre_match_count': 0,
            'actor_match_count': 0,
            'director_match': 0,
            'vote_average': 8.5,
            'liked': 0
        })

    # 3. Low-rated movies even if there is some genre match (teaches tree that bad rating = disliked)
    for _ in range(5):
        train_features.append({
            'genre_match_count': 1,
            'actor_match_count': 0,
            'director_match': 0,
            'vote_average': 3.0,
            'liked': 0
        })

    # Build pandas DataFrame
    df = pd.DataFrame(train_features)
    X_train = df[['genre_match_count', 'actor_match_count', 'director_match', 'vote_average']]
    y_train = df['liked']
    # Instantiate and train DecisionTreeClassifier (max_depth=4 to support all features)
    clf = DecisionTreeClassifier(max_depth=4, random_state=42)
    clf.fit(X_train, y_train)

    # Perform probabilistic predictions on candidates
    scored_candidates = []
    for c in candidates:
        feats = extract_features(c)
        features_df = pd.DataFrame([feats])
        features_df = features_df[['genre_match_count', 'actor_match_count', 'director_match', 'vote_average']]
        proba = clf.predict_proba(features_df)[0]
        
        # Safely locate the probability for class 1
        class_1_idx = np.where(clf.classes_ == 1)[0]
        score = float(proba[class_1_idx[0]]) if len(class_1_idx) > 0 else 0.0

        c_copy = dict(c)
        c_copy['recommendation_score'] = score
        scored_candidates.append(c_copy)

    # Print final output in JSON format
    print(json.dumps(scored_candidates, ensure_ascii=False))

if __name__ == '__main__':
    main()
