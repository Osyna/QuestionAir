import numpy as np
from typing import List, Dict, Set
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
import spacy
import ollama
from sklearn.feature_extraction.text import TfidfVectorizer
import re


class KeywordExtractor:
    def __init__(self, embedding_model: str = "nomic-embed-text"):
        """Initialize the keyword extractor with specified embedding model."""
        self.embedding_model = embedding_model
        # Load French language model for spaCy
        try:
            self.nlp = spacy.load('fr_core_news_md')
        except:
            print("Downloading French language model...")
            spacy.cli.download('fr_core_news_md')
            self.nlp = spacy.load('fr_core_news_md')

        # Keep a cache of embeddings to avoid recomputing
        self.embedding_cache: Dict[str, np.ndarray] = {}
        # Keep a cache of aligned keywords
        self.keyword_alignment_cache: Dict[str, str] = {}

    def get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for a piece of text using ollama."""
        if text in self.embedding_cache:
            return self.embedding_cache[text]

        response = ollama.embeddings(
                model = self.embedding_model,
                prompt = text
                )
        embedding = np.array(response['embedding'])
        self.embedding_cache[text] = embedding
        return embedding

    def extract_keywords(self, text: str, num_keywords: int = 3) -> List[str]:
        """Extract keywords from text using a combination of methods."""
        # Clean and preprocess text
        doc = self.nlp(text)

        # Extract candidates using multiple methods
        candidates = set()

        # Method 1: spaCy NER
        for ent in doc.ents:
            candidates.add(ent.text.lower())

        # Method 2: Noun phrases
        for chunk in doc.noun_chunks:
            candidates.add(chunk.text.lower())

        # Method 3: Important POS tags (nouns, proper nouns, etc.)
        important_pos = {'NOUN', 'PROPN', 'ADJ'}
        for token in doc:
            if token.pos_ in important_pos:
                candidates.add(token.text.lower())

        # Method 4: TF-IDF for single words
        tfidf = TfidfVectorizer(max_features = 10)
        try:
            tfidf_matrix = tfidf.fit_transform([text])
            word_scores = dict(zip(tfidf.get_feature_names_out(), tfidf_matrix.toarray()[0]))
            candidates.update(word_scores.keys())
        except:
            pass

        # Filter out very short keywords and those with special characters
        candidates = {k for k in candidates
                      if len(k) > 2 and re.match(r'^[a-zA-ZÀ-ÿ\s-]+$', k)}

        # Get embeddings for all candidates
        candidate_embeddings = {k: self.get_embedding(k) for k in candidates}

        # Get embedding for the full text
        text_embedding = self.get_embedding(text)

        # Score candidates based on similarity to full text
        scores = {k: cosine_similarity(v.reshape(1, -1),
                                       text_embedding.reshape(1, -1))[0][0]
                  for k, v in candidate_embeddings.items()}

        # Sort by score and take top keywords
        top_keywords = sorted(scores.items(), key = lambda x: x[1], reverse = True)
        return [k for k, _ in top_keywords[:num_keywords]]

    def align_keywords(self, keywords: List[str], threshold: float = 0.85) -> List[str]:
        """Align similar keywords to their most common form."""
        if not keywords:
            return []

        # Check cache first
        if all(k in self.keyword_alignment_cache for k in keywords):
            return [self.keyword_alignment_cache[k] for k in keywords]

        # Get embeddings for all keywords
        embeddings = {k: self.get_embedding(k) for k in keywords}

        # Calculate similarity matrix
        n = len(keywords)
        similarity_matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(i + 1, n):
                sim = cosine_similarity(
                        embeddings[keywords[i]].reshape(1, -1),
                        embeddings[keywords[j]].reshape(1, -1)
                        )[0][0]
                similarity_matrix[i][j] = sim
                similarity_matrix[j][i] = sim

        # Cluster similar keywords
        clusters: List[Set[str]] = []
        used = set()

        for i in range(n):
            if keywords[i] in used:
                continue

            cluster = {keywords[i]}
            used.add(keywords[i])

            for j in range(n):
                if i != j and similarity_matrix[i][j] >= threshold:
                    cluster.add(keywords[j])
                    used.add(keywords[j])

            clusters.append(cluster)

        # For each cluster, select the most representative keyword
        aligned_keywords = []
        for cluster in clusters:
            # Use the most frequent keyword in the original list as representative
            counts = Counter(k for k in keywords if k in cluster)
            representative = max(counts.items(), key = lambda x: x[1])[0]

            # Update cache
            for k in cluster:
                self.keyword_alignment_cache[k] = representative

            aligned_keywords.append(representative)

        return aligned_keywords