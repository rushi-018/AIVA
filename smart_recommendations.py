"""
smart_recommendations.py: Intelligent product recommendation system using AI
"""
import re
import numpy as np
from typing import List, Dict, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class SmartProductRecommender:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
        
    def extract_features(self, product: Dict) -> Dict:
        """Extract meaningful features from product data."""
        title = product.get('title', '').lower()
        price = product.get('price', 0)
        rating = product.get('rating', 0)
        
        features = {
            'price': price,
            'rating': float(rating) if rating else 0,
            'title_length': len(title),
            'has_brand': self._has_known_brand(title),
            'is_wireless': any(word in title for word in ['wireless', 'bluetooth', 'bt']),
            'is_gaming': any(word in title for word in ['gaming', 'gamer', 'game']),
            'has_mic': any(word in title for word in ['mic', 'microphone']),
            'is_premium': any(word in title for word in ['premium', 'pro', 'ultra', 'max']),
            'word_count': len(title.split())
        }
        
        return features
    
    def _has_known_brand(self, title: str) -> bool:
        """Check if product has a known brand."""
        brands = [
            'sony', 'jbl', 'boat', 'realme', 'samsung', 'apple', 'oneplus', 
            'mi', 'redmi', 'poco', 'oppo', 'vivo', 'noise', 'zebronics',
            'boult', 'ptron', 'fire-boltt', 'amazfit', 'fossil'
        ]
        return any(brand in title.lower() for brand in brands)
    
    def calculate_relevance_score(self, products: List[Dict], user_query: str) -> List[Dict]:
        """Calculate relevance score based on user query and product features."""
        if not products:
            return products
        
        # Prepare text data for semantic similarity
        product_texts = [p.get('title', '') for p in products]
        all_texts = product_texts + [user_query]
        
        try:
            # Calculate TF-IDF similarity
            tfidf_matrix = self.vectorizer.fit_transform(all_texts)
            query_vector = tfidf_matrix[-1:]  # Last vector is the query
            product_vectors = tfidf_matrix[:-1]  # All except query
            
            # Calculate cosine similarity
            similarities = cosine_similarity(query_vector, product_vectors).flatten()
        except Exception:
            # Fallback: use simple keyword matching
            similarities = [self._simple_similarity(user_query, p.get('title', '')) for p in products]
        
        # Add features and calculate composite scores
        for i, product in enumerate(products):
            features = self.extract_features(product)
            
            # Base relevance from text similarity
            relevance = similarities[i] if i < len(similarities) else 0
            
            # Boost score based on features
            score_boosts = {
                'has_brand': 0.2,  # Brand products get boost
                'has_rating': 0.1 if features['rating'] > 0 else 0,
                'good_rating': 0.3 if features['rating'] >= 4.0 else 0,
                'reasonable_price': 0.1,  # Will be calculated
                'feature_rich': 0.1 if features['word_count'] > 5 else 0
            }
            
            # Calculate reasonable price boost (not too cheap, not too expensive)
            prices = [p.get('price', 0) for p in products if p.get('price')]
            if prices:
                avg_price = sum(prices) / len(prices)
                price_ratio = features['price'] / avg_price if avg_price > 0 else 1
                if 0.5 <= price_ratio <= 1.5:  # Within reasonable range
                    score_boosts['reasonable_price'] = 0.15
            
            # Apply boosts
            total_boost = sum([
                score_boosts['has_brand'] if features['has_brand'] else 0,
                score_boosts['has_rating'],
                score_boosts['good_rating'],
                score_boosts['reasonable_price'],
                score_boosts['feature_rich']
            ])
            
            final_score = relevance + total_boost
            
            # Add scoring info to product
            product['relevance_score'] = relevance
            product['feature_score'] = total_boost
            product['final_score'] = final_score
            product['features'] = features
        
        return products
    
    def _simple_similarity(self, query: str, title: str) -> float:
        """Simple keyword-based similarity fallback."""
        query_words = set(query.lower().split())
        title_words = set(title.lower().split())
        
        if not query_words:
            return 0
        
        intersection = query_words.intersection(title_words)
        return len(intersection) / len(query_words)
    
    def recommend_products(self, products: List[Dict], user_query: str, 
                         criteria: str = "smart", top_k: int = 5) -> List[Dict]:
        """Main recommendation function."""
        if not products:
            return []
        
        # Calculate relevance scores
        scored_products = self.calculate_relevance_score(products, user_query)
        
        # Sort based on criteria
        if criteria == "price":
            # Sort by price (ascending)
            scored_products.sort(key=lambda x: x.get('price', float('inf')))
        elif criteria == "rating":
            # Sort by rating (descending), then price (ascending)
            scored_products.sort(key=lambda x: (-x.get('features', {}).get('rating', 0), x.get('price', float('inf'))))
        elif criteria == "smart":
            # Sort by AI relevance score (descending)
            scored_products.sort(key=lambda x: -x.get('final_score', 0))
        else:
            # Default: smart sorting
            scored_products.sort(key=lambda x: -x.get('final_score', 0))
        
        return scored_products[:top_k]
    
    def explain_recommendation(self, product: Dict) -> str:
        """Explain why this product was recommended."""
        features = product.get('features', {})
        
        reasons = []
        
        if features.get('has_brand'):
            reasons.append("trusted brand")
        
        if features.get('rating', 0) >= 4.0:
            reasons.append(f"high rating ({features['rating']}⭐)")
        elif features.get('rating', 0) > 0:
            reasons.append(f"rated {features['rating']}⭐")
        
        if product.get('relevance_score', 0) > 0.3:
            reasons.append("good match for your search")
        
        if features.get('is_wireless'):
            reasons.append("wireless/bluetooth")
        
        if features.get('has_mic'):
            reasons.append("has microphone")
        
        if features.get('is_gaming'):
            reasons.append("gaming optimized")
        
        if not reasons:
            reasons.append("good value option")
        
        return "Recommended because: " + ", ".join(reasons)

# Test function
if __name__ == "__main__":
    recommender = SmartProductRecommender()
    
    # Test with sample products
    sample_products = [
        {"title": "Sony WH-CH720N Wireless Noise Canceling Headphones", "price": 8990, "rating": 4.2},
        {"title": "JBL Tune 760NC Wireless Over-Ear Headphones", "price": 7999, "rating": 4.1},
        {"title": "Generic Bluetooth Earphones", "price": 299, "rating": 3.2},
        {"title": "BOAT Rockerz 450 Bluetooth Headphones", "price": 1999, "rating": 4.0},
        {"title": "Premium Gaming Headset with RGB", "price": 3499, "rating": 3.8}
    ]
    
    user_query = "best wireless headphones for music"
    
    recommendations = recommender.recommend_products(sample_products, user_query, criteria="smart")
    
    print("🤖 Smart Recommendations:")
    for i, product in enumerate(recommendations, 1):
        print(f"{i}. {product['title']} - ₹{product['price']}")
        print(f"   {recommender.explain_recommendation(product)}")
        print(f"   Score: {product.get('final_score', 0):.3f}")
        print()