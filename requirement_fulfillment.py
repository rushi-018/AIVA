from dataclasses import dataclass
from typing import List, Dict, Optional
import re

@dataclass
class UserRequirement:
    product_name: str
    quantity: int = 1
    category: str = "general"
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    features: Optional[List[str]] = None
    brand_preference: Optional[List[str]] = None

class RequirementAnalyzer:
    def analyze_query(self, query):
        query_lower = query.lower()
        
        # Extract budget information
        budget_min = None
        budget_max = None
        
        # Look for budget patterns like "under 5000", "between 1000 and 3000", "budget 2000"
        budget_patterns = [
            r'under\s+(\d+)',
            r'below\s+(\d+)', 
            r'budget\s+(\d+)',
            r'(\d+)\s*rupees?',
            r'rs\.?\s*(\d+)',
            r'₹\s*(\d+)',
            r'between\s+(\d+)\s+and\s+(\d+)',
            r'from\s+(\d+)\s+to\s+(\d+)'
        ]
        
        for pattern in budget_patterns:
            matches = re.findall(pattern, query_lower)
            if matches:
                if 'between' in pattern or 'from' in pattern:
                    # Range pattern
                    budget_min = float(matches[0][0])
                    budget_max = float(matches[0][1])
                else:
                    # Single value pattern
                    if 'under' in pattern or 'below' in pattern:
                        budget_max = float(matches[0])
                    else:
                        budget_min = float(matches[0])
                break
        
        # Extract category
        category = "general"
        categories = {
            'electronics': ['laptop', 'phone', 'mobile', 'computer', 'tablet', 'headphones', 'camera'],
            'grocery': ['rice', 'milk', 'bread', 'fruit', 'vegetable', 'oil', 'sugar', 'food'],
            'clothing': ['shirt', 'pants', 'dress', 'shoes', 'jacket', 'clothes'],
            'books': ['book', 'novel', 'textbook', 'magazine'],
            'home': ['furniture', 'chair', 'table', 'bed', 'sofa']
        }
        
        for cat, keywords in categories.items():
            if any(keyword in query_lower for keyword in keywords):
                category = cat
                break
        
        # Extract features
        features = []
        feature_keywords = ['wireless', 'bluetooth', 'fast', 'organic', 'premium', 'latest', 'new']
        for keyword in feature_keywords:
            if keyword in query_lower:
                features.append(keyword)
        
        # Extract brand preferences
        brands = []
        brand_keywords = ['apple', 'samsung', 'hp', 'dell', 'nike', 'adidas', 'sony', 'lg']
        for brand in brand_keywords:
            if brand in query_lower:
                brands.append(brand)
        
        return UserRequirement(
            product_name=query, 
            quantity=1,
            category=category,
            budget_min=budget_min,
            budget_max=budget_max,
            features=features if features else None,
            brand_preference=brands if brands else None
        )

class ProductRecommendationEngine:
    def __init__(self, analyzer):
        self.analyzer = analyzer
        
        # Amazon-specific ranking factors
        self.amazon_ranking_weights = {
            'price_match': 0.4,      # How well price matches budget
            'brand_match': 0.25,     # Brand preference match
            'feature_match': 0.2,    # Feature keyword match
            'rating_boost': 0.1,     # Higher ratings get boost
            'prime_boost': 0.05      # Prime eligible boost
        }
        
        # Category-specific preferences
        self.category_preferences = {
            'electronics': ['latest', 'warranty', 'certified', 'genuine'],
            'clothing': ['size', 'material', 'brand', 'style'],
            'books': ['edition', 'author', 'reviews', 'bestseller'],
            'home': ['quality', 'durable', 'easy', 'assembly']
        }
    
    def rank_products(self, products, requirements):
        """Enhanced ranking system with Amazon-specific intelligence"""
        if not products:
            return []
        
        print(f"🎯 Ranking {len(products)} products for Amazon...")
        
        # Enhanced filtering and scoring
        scored_products = []
        
        for product in products:
            score = self._calculate_product_score(product, requirements)
            if score > 0:  # Only include products with positive scores
                product['_ranking_score'] = score
                scored_products.append(product)
        
        # Sort by score (descending - highest score first)
        scored_products.sort(key=lambda p: p.get('_ranking_score', 0), reverse=True)
        
        print(f"✅ Ranked products - Top choice: {scored_products[0]['title'][:40]}... (Score: {scored_products[0]['_ranking_score']:.2f})")
        
        return scored_products
    
    def _calculate_product_score(self, product, requirements):
        """Calculate ranking score for a product"""
        score = 0.0
        title = product.get('title', '').lower()
        price = product.get('price', 0)
        
        # 1. Price matching score
        price_score = self._calculate_price_score(price, requirements)
        score += price_score * self.amazon_ranking_weights['price_match']
        
        # 2. Brand preference matching
        if requirements.brand_preference:
            brand_score = self._calculate_brand_score(title, requirements.brand_preference)
            score += brand_score * self.amazon_ranking_weights['brand_match']
        
        # 3. Feature matching
        if requirements.features:
            feature_score = self._calculate_feature_score(title, requirements.features)
            score += feature_score * self.amazon_ranking_weights['feature_match']
        
        # 4. Category-specific preferences
        category_score = self._calculate_category_score(title, requirements.category)
        score += category_score * self.amazon_ranking_weights['feature_match']
        
        # 5. Amazon-specific bonuses
        amazon_score = self._calculate_amazon_bonuses(title)
        score += amazon_score * self.amazon_ranking_weights['rating_boost']
        
        # Ensure minimum score for budget-compliant products
        if self._is_within_budget(price, requirements):
            score = max(score, 0.3)  # Minimum score for budget-compliant items
        else:
            score = 0  # Exclude if outside budget
        
        return score
    
    def _calculate_price_score(self, price, requirements):
        """Score based on how well price fits budget"""
        if price <= 0:
            return 0
        
        # If no budget specified, prefer mid-range items
        if not requirements.budget_min and not requirements.budget_max:
            return 0.5
        
        budget_min = requirements.budget_min or 0
        budget_max = requirements.budget_max or float('inf')
        
        if price < budget_min or price > budget_max:
            return 0  # Outside budget
        
        # Score higher for prices closer to the middle of budget range
        if budget_max != float('inf'):
            budget_middle = (budget_min + budget_max) / 2
            distance_from_middle = abs(price - budget_middle)
            max_distance = (budget_max - budget_min) / 2
            return 1.0 - (distance_from_middle / max_distance) if max_distance > 0 else 1.0
        else:
            # Only minimum budget specified - prefer higher value items
            return min(1.0, price / (budget_min * 2)) if budget_min > 0 else 0.5
    
    def _calculate_brand_score(self, title, preferred_brands):
        """Score based on brand preference match"""
        for brand in preferred_brands:
            if brand.lower() in title:
                return 1.0
        return 0.0
    
    def _calculate_feature_score(self, title, required_features):
        """Score based on feature keyword match"""
        matched_features = 0
        for feature in required_features:
            if feature.lower() in title:
                matched_features += 1
        
        return matched_features / len(required_features) if required_features else 0
    
    def _calculate_category_score(self, title, category):
        """Score based on category-specific keywords"""
        if category not in self.category_preferences:
            return 0
        
        category_keywords = self.category_preferences[category]
        matched_keywords = 0
        
        for keyword in category_keywords:
            if keyword in title:
                matched_keywords += 1
        
        return matched_keywords / len(category_keywords) if category_keywords else 0
    
    def _calculate_amazon_bonuses(self, title):
        """Amazon-specific bonuses"""
        score = 0
        
        # Bonus for Amazon Choice, bestseller, etc.
        amazon_badges = ['choice', 'bestseller', 'prime', 'highly rated', 'top rated']
        for badge in amazon_badges:
            if badge in title:
                score += 0.1
        
        return min(score, 0.5)  # Cap bonus at 0.5
    
    def _is_within_budget(self, price, requirements):
        """Check if price is within budget"""
        if price <= 0:
            return False
        
        budget_min = requirements.budget_min or 0
        budget_max = requirements.budget_max or float('inf')
        
        return budget_min <= price <= budget_max

class SatisfactionChecker:
    def __init__(self, analyzer):
        self.analyzer = analyzer
    
    def check_satisfaction(self, products, requirements):
        """Enhanced satisfaction checking with detailed analysis"""
        if not products:
            return {
                'satisfied': False, 
                'score': 0.0,
                'reason': 'No products found matching your requirements'
            }
        
        # Analyze product quality and match
        total_products = len(products)
        budget_compliant = self._count_budget_compliant(products, requirements)
        
        # Calculate satisfaction score
        base_score = min(0.8, total_products / 10)  # More products = higher satisfaction
        budget_score = budget_compliant / total_products if total_products > 0 else 0
        
        # Get best product (highest ranking score)
        best_product = products[0] if products else None
        
        # Select diverse alternatives (different price ranges)
        alternatives = self._select_diverse_alternatives(products[1:], requirements)
        
        # Generate satisfaction message
        satisfaction_score = (base_score + budget_score) / 2
        
        if satisfaction_score >= 0.7:
            reason = f"Excellent match! Found {total_products} products, {budget_compliant} within budget"
            satisfied = True
        elif satisfaction_score >= 0.5:
            reason = f"Good selection found: {total_products} products, {budget_compliant} within budget range"
            satisfied = True
        else:
            reason = f"Limited options: {total_products} products found, consider adjusting budget"
            satisfied = False
        
        # Add specific recommendations
        recommendations = self._generate_recommendations(products, requirements)
        
        return {
            'satisfied': satisfied,
            'score': satisfaction_score,
            'reason': reason,
            'best_product': best_product,
            'alternatives': alternatives,
            'recommendations': recommendations,
            'stats': {
                'total_products': total_products,
                'budget_compliant': budget_compliant,
                'avg_price': sum(p.get('price', 0) for p in products) / total_products if products else 0
            }
        }
    
    def _count_budget_compliant(self, products, requirements):
        """Count products within budget"""
        budget_min = requirements.budget_min or 0
        budget_max = requirements.budget_max or float('inf')
        
        count = 0
        for product in products:
            price = product.get('price', 0)
            if budget_min <= price <= budget_max:
                count += 1
        
        return count
    
    def _select_diverse_alternatives(self, products, requirements, max_alternatives=3):
        """Select diverse alternatives across different price ranges"""
        if not products:
            return []
        
        # Sort by price
        sorted_products = sorted(products, key=lambda p: p.get('price', 0))
        alternatives = []
        
        # Try to get products from different price segments
        total = len(sorted_products)
        if total > 0:
            # Low price option
            if total > 0:
                alternatives.append(sorted_products[0])
            
            # Mid price option
            if total > 2:
                mid_index = total // 2
                alternatives.append(sorted_products[mid_index])
            
            # Higher price option (if different from others)
            if total > 1 and len(alternatives) < max_alternatives:
                high_product = sorted_products[-1]
                if high_product not in alternatives:
                    alternatives.append(high_product)
        
        return alternatives[:max_alternatives]
    
    def _generate_recommendations(self, products, requirements):
        """Generate specific recommendations"""
        recommendations = []
        
        if not products:
            return ["Try broader search terms", "Consider increasing budget range"]
        
        avg_price = sum(p.get('price', 0) for p in products) / len(products)
        
        # Budget recommendations
        if requirements.budget_max and avg_price > requirements.budget_max:
            recommendations.append(f"Consider increasing budget - average price is ₹{avg_price:.0f}")
        elif requirements.budget_min and avg_price < requirements.budget_min:
            recommendations.append("Great value options available within your budget")
        
        # Feature recommendations
        if requirements.features:
            feature_coverage = self._calculate_feature_coverage(products, requirements.features)
            if feature_coverage < 0.5:
                recommendations.append("Consider adjusting feature requirements for more options")
        
        # Brand recommendations
        if requirements.brand_preference:
            brand_availability = self._check_brand_availability(products, requirements.brand_preference)
            if not brand_availability:
                recommendations.append("Preferred brands not found - consider alternative brands")
        
        return recommendations
    
    def _calculate_feature_coverage(self, products, required_features):
        """Calculate what percentage of products have required features"""
        if not required_features:
            return 1.0
        
        feature_matches = 0
        for product in products:
            title = product.get('title', '').lower()
            if any(feature.lower() in title for feature in required_features):
                feature_matches += 1
        
        return feature_matches / len(products) if products else 0
    
    def _check_brand_availability(self, products, preferred_brands):
        """Check if any preferred brands are available"""
        for product in products:
            title = product.get('title', '').lower()
            if any(brand.lower() in title for brand in preferred_brands):
                return True
        return False
