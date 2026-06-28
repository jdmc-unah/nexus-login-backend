// Machine Learning Recommendation Engine in Pure Javascript
// Replaces recommender.py for Cloudflare Workers compatibility

function getGini(rows) {
  if (rows.length === 0) return 0;
  let count1 = 0;
  for (const r of rows) {
    if (r.liked === 1) count1++;
  }
  const p1 = count1 / rows.length;
  const p0 = 1 - p1;
  return 1 - (p0 * p0 + p1 * p1);
}

function split(rows, feature, value) {
  const left = [];
  const right = [];
  for (const r of rows) {
    if (r[feature] <= value) {
      left.push(r);
    } else {
      right.push(r);
    }
  }
  return { left, right };
}

function buildTree(rows, depth, maxDepth) {
  const total = rows.length;
  if (total === 0) return { isLeaf: true, proba: 0 };
  
  let count1 = 0;
  for (const r of rows) {
    if (r.liked === 1) count1++;
  }
  const proba = count1 / total;
  
  // Base case
  if (depth >= maxDepth || count1 === 0 || count1 === total) {
    return { isLeaf: true, proba };
  }
  
  const features = ['genre_match_count', 'actor_match_count', 'director_match', 'vote_average'];
  let bestGini = getGini(rows);
  let bestSplit = null;
  
  for (const f of features) {
    // Get unique sorted values for this feature
    const values = Array.from(new Set(rows.map(r => r[f]))).sort((a, b) => a - b);
    for (let i = 0; i < values.length - 1; i++) {
      const val = (values[i] + values[i + 1]) / 2; // Midpoint split
      const { left, right } = split(rows, f, val);
      if (left.length === 0 || right.length === 0) continue;
      
      const gini = (left.length / total) * getGini(left) + (right.length / total) * getGini(right);
      if (gini < bestGini) {
        bestGini = gini;
        bestSplit = { feature: f, value: val, left, right };
      }
    }
  }
  
  if (!bestSplit) {
    return { isLeaf: true, proba };
  }
  
  return {
    isLeaf: false,
    feature: bestSplit.feature,
    value: bestSplit.value,
    left: buildTree(bestSplit.left, depth + 1, maxDepth),
    right: buildTree(bestSplit.right, depth + 1, maxDepth)
  };
}

function predict(node, features) {
  if (node.isLeaf) {
    return node.proba;
  }
  if (features[node.feature] <= node.value) {
    return predict(node.left, features);
  } else {
    return predict(node.right, features);
  }
}

function recommend(history = [], candidates = []) {
  // If history is empty, populate with some default mock items so the tree can train
  if (!history || history.length === 0) {
    history = [
      { id: 1, genre_ids: [28, 12], vote_average: 8.5, cast: ["Robert Downey Jr.", "Chris Evans"], directors: ["Anthony Russo"] },
      { id: 2, genre_ids: [35, 10751], vote_average: 8.0, cast: ["Jim Carrey"], directors: ["Tom Shadyac"] },
      { id: 3, genre_ids: [28, 53], vote_average: 9.0, cast: ["Christian Bale"], directors: ["Christopher Nolan"] }
    ];
  }

  // Extract user profile from history
  const likedGenres = [];
  const likedActors = [];
  const likedDirectors = [];
  
  for (const m of history) {
    const genreIds = m.genre_ids || [];
    for (const g of genreIds) {
      likedGenres.push(g);
    }
    const cast = m.cast || [];
    for (const actor of cast) {
      likedActors.push(actor);
    }
    const directors = m.directors || [];
    for (const director of directors) {
      likedDirectors.push(director);
    }
  }

  const likedGenresSet = new Set(likedGenres);
  const likedActorsSet = new Set(likedActors);
  const likedDirectorsSet = new Set(likedDirectors);

  function extractFeatures(movie) {
    const genreIds = movie.genre_ids || [];
    const movieGenres = genreIds.slice(0, 3);
    const genreMatchCount = movieGenres.filter(g => likedGenresSet.has(g)).length;
    
    const cast = movie.cast || [];
    const actorMatchCount = cast.filter(a => likedActorsSet.has(a)).length;
    
    const directors = movie.directors || [];
    const directorMatch = directors.some(d => likedDirectorsSet.has(d)) ? 1 : 0;
    
    const voteAverage = parseFloat(movie.vote_average || 0.0);
    
    return {
      genre_match_count: genreMatchCount,
      actor_match_count: actorMatchCount,
      director_match: directorMatch,
      vote_average: voteAverage
    };
  }

  const trainFeatures = [];
  
  // Process positive history
  for (const m of history) {
    const feats = extractFeatures(m);
    feats.liked = 1;
    trainFeatures.push(feats);
  }
  
  // Generate synthetic negative examples (liked = 0)
  for (let i = 0; i < 10; i++) {
    trainFeatures.push({
      genre_match_count: 0,
      actor_match_count: 0,
      director_match: 0,
      vote_average: 5.5,
      liked: 0
    });
  }
  for (let i = 0; i < 5; i++) {
    trainFeatures.push({
      genre_match_count: 0,
      actor_match_count: 0,
      director_match: 0,
      vote_average: 8.5,
      liked: 0
    });
  }
  for (let i = 0; i < 5; i++) {
    trainFeatures.push({
      genre_match_count: 1,
      actor_match_count: 0,
      director_match: 0,
      vote_average: 3.0,
      liked: 0
    });
  }

  // Train decision tree
  const tree = buildTree(trainFeatures, 0, 4);

  // Score candidates
  const scoredCandidates = candidates.map(c => {
    const feats = extractFeatures(c);
    const score = predict(tree, feats);
    return {
      ...c,
      recommendation_score: score
    };
  });

  return scoredCandidates;
}

export { recommend };
