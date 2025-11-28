import sys
from pathlib import Path
import re
from typing import Optional

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TurkishPreprocessor:
    """Turkish text preprocessing with broad synonym expansion"""
    
    def __init__(self):
        self.turkish_to_english = {
            "oto": "auto",
            "otomobil": "automobile",
            "kredi": "credit",
            "kampanya": "campaign",
            "kampanyası": "campaign",
            "kampanyaları": "campaigns",
        }
        
        self.common_patterns = [
            (r'\boto\b', 'auto'),
            (r'\bautoking\b', 'auto king'),
            (r'\bauto-king\b', 'auto king'),
            (r'\bauto_king\b', 'auto king'),
        ]
    
    def _normalize_term(self, term: str) -> str:
        """Normalize term by removing punctuation and standardizing"""
        normalized = re.sub(r'[-_\s]+', ' ', term.lower())
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized
    
    def _generate_variations(self, term: str) -> set:
        """Generate all possible variations of a term"""
        variations = set()
        term_lower = term.lower()
        
        variations.add(term_lower)
        variations.add(term_lower.replace(' ', '-'))
        variations.add(term_lower.replace(' ', '_'))
        variations.add(term_lower.replace('-', ' '))
        variations.add(term_lower.replace('_', ' '))
        variations.add(term_lower.replace(' ', ''))
        
        if ' ' in term_lower:
            words = term_lower.split()
            variations.add(''.join(words))
            variations.add('-'.join(words))
            variations.add('_'.join(words))
            variations.add(''.join(w.capitalize() for w in words))
            variations.add(''.join(w[0].upper() + w[1:] if len(w) > 1 else w.upper() for w in words))
        
        return variations
    
    def _find_turkish_english_match(self, query: str) -> Optional[str]:
        """Find Turkish-English word matches algorithmically"""
        query_lower = query.lower()
        words = re.findall(r'\b\w+\b', query_lower)
        
        for word in words:
            if word in self.turkish_to_english:
                english_word = self.turkish_to_english[word]
                return query_lower.replace(word, english_word)
        
        return None
    
    def preprocess_query(self, query: str) -> str:
        """Preprocess query with broad synonym expansion"""
        processed = query
        query_lower = query.lower()
        
        normalized_query = self._normalize_term(query)
        query_variations = self._generate_variations(normalized_query)
        
        turkish_english_match = self._find_turkish_english_match(query)
        if turkish_english_match:
            processed = turkish_english_match
        
        for pattern, replacement in self.common_patterns:
            if re.search(pattern, query_lower):
                processed = re.sub(pattern, replacement, processed, flags=re.IGNORECASE)
                break
        
        processed = processed.strip()
        
        if processed.lower() != query.lower():
            logger.debug(f"Query expanded: '{query}' -> '{processed}'")
        
        return processed
    
    def find_synonym_in_text(self, query: str, text: str) -> bool:
        """Check if query or its variations exist in text"""
        query_variations = self._generate_variations(query)
        processed_query = self.preprocess_query(query)
        processed_variations = self._generate_variations(processed_query)
        
        all_variations = query_variations | processed_variations
        text_lower = text.lower()
        
        for variation in all_variations:
            if len(variation) > 2 and variation in text_lower:
                return True
        
        return False
    
    def normalize_text(self, text: str) -> str:
        """Normalize Turkish text"""
        text = re.sub(r"\s+", " ", text)
        text = text.strip()
        return text

