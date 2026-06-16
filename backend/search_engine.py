import json
import os
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class NidanaSearchEngine:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), "data", "disease_db.json")
        
        self.db_path = db_path
        self.diseases = []
        self.load_database()
        self.initialize_vectorizer()

    def load_database(self):
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Disease database not found at {self.db_path}")
            
        with open(self.db_path, "r", encoding="utf-8") as f:
            self.diseases = json.load(f)
        print(f"Loaded {len(self.diseases)} diseases into search engine.")

    def initialize_vectorizer(self):
        # Build search documents
        # We combine Roga name, symptoms (ayurvedic + modern), causes, and retrieval document
        self.search_docs = []
        for disease in self.diseases:
            # Gather symptoms
            symptoms_text = " ".join(disease["lakshana"])
            modern_syms = []
            for mapping in disease.get("symptom_mapping", []):
                modern_syms.extend(mapping.get("modern_equivalents", []))
            modern_text = " ".join(modern_syms)
            
            nidana_text = " ".join(disease["nidana"])
            dosha_text = " ".join(disease["dosha"])
            dushya_text = " ".join(disease["dushya"])
            srotas_text = " ".join(disease["srotas"])
            
            # Combine all text
            doc = (
                f"{disease['roga']} "
                f"{symptoms_text} "
                f"{modern_text} "
                f"{nidana_text} "
                f"{dosha_text} "
                f"{dushya_text} "
                f"{srotas_text} "
                f"{disease['samprapti']} "
                f"{disease['retrieval_document']}"
            )
            # Simple normalization (lowercase)
            self.search_docs.append(doc.lower())
            
        # Fit vectorizer
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = self.vectorizer.fit_transform(self.search_docs)

    def search(self, query, top_n=5):
        if not query or not query.strip():
            return []
            
        query_norm = query.lower()
        query_vec = self.vectorizer.transform([query_norm])
        
        # Calculate TF-IDF Cosine Similarity
        cos_similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        results = []
        for idx, score in enumerate(cos_similarities):
            disease = self.diseases[idx]
            
            # Perform additional symptom keyword matching to boost scores and identify matches
            matched_symptoms = []
            keyword_matches = 0
            
            # Check for modern symptom matches
            for mapping in disease.get("symptom_mapping", []):
                ayur_term = mapping["ayurvedic_term"].lower()
                for mod_eq in mapping["modern_equivalents"]:
                    mod_eq_norm = mod_eq.lower()
                    # If the modern equivalent is in the query (e.g. "shivering" matches query "patient is shivering")
                    if re.search(r'\b' + re.escape(mod_eq_norm) + r'\b', query_norm) or mod_eq_norm in query_norm:
                        matched_symptoms.append({
                            "ayurvedic_term": mapping["ayurvedic_term"],
                            "matched_term": mod_eq,
                            "type": "modern"
                        })
                        keyword_matches += 1
                        break # count once per ayurvedic term
                else:
                    # Check if the ayurvedic term itself is in the query (e.g. "vepathu")
                    if re.search(r'\b' + re.escape(ayur_term) + r'\b', query_norm) or ayur_term in query_norm:
                        matched_symptoms.append({
                            "ayurvedic_term": mapping["ayurvedic_term"],
                            "matched_term": mapping["ayurvedic_term"],
                            "type": "ayurvedic"
                        })
                        keyword_matches += 1
            
            # Check for general keywords in the lakshana array as fallback
            for lak in disease["lakshana"]:
                lak_norm = lak.lower()
                if lak_norm in query_norm and not any(m["ayurvedic_term"].lower() in lak_norm for m in matched_symptoms):
                    matched_symptoms.append({
                        "ayurvedic_term": lak,
                        "matched_term": lak,
                        "type": "ayurvedic_raw"
                    })
                    keyword_matches += 0.5
            
            # Check if Roga name itself is in query
            roga_match = False
            if disease["roga"].lower() in query_norm:
                roga_match = True
                keyword_matches += 2.0
                
            # Apply boost for keyword matches
            final_score = float(score)
            if keyword_matches > 0:
                # Boost formula: initial score + 0.1 * number of keyword matches (up to 0.9 max boost)
                final_score = min(1.0, final_score + 0.12 * min(keyword_matches, 5))
            
            # Ensure even without TF-IDF matches, high keyword matches yield results
            if keyword_matches > 0 and final_score < 0.1:
                final_score = 0.1 + 0.05 * min(keyword_matches, 5)
                
            # Round score
            final_score = round(final_score, 4)
            
            results.append({
                "disease": disease,
                "score": final_score,
                "matched_symptoms": matched_symptoms,
                "keyword_matches": keyword_matches,
                "roga_match": roga_match
            })
            
        # Sort results by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_n]

if __name__ == "__main__":
    # Test search engine locally
    engine = NidanaSearchEngine()
    test_queries = [
        "Patient has high fever and is shivering with dry lips",
        "Joint pain and morning stiffness with swelling in knees",
        "Yellow discoloration of eyes and skin with dark urine",
        "radiating pain from hip down through the leg with numbness"
    ]
    for q in test_queries:
        print(f"\nQuery: '{q}'")
        res = engine.search(q, top_n=2)
        for r in res:
            print(f"  - Match: {r['disease']['roga']} (Score: {r['score']}, Matched Syms: {[m['matched_term'] for m in r['matched_symptoms']]})")
