import sys
from pathlib import Path
import os

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import logging
from typing import List, Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv
from services.rag.preprocessing import TurkishPreprocessor

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResponseGenerator:
    def __init__(self, use_openai: bool = True):
        self.use_openai = use_openai
        self.openai_client = None
        self.model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        self.preprocessor = TurkishPreprocessor()
        
        if use_openai:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
                logger.info(f"OpenAI client initialized with model: {self.model}")
            else:
                logger.warning("OPENAI_API_KEY not found in .env file, falling back to template-based generation")
                self.use_openai = False
        
        self.templates = {
            "default": """Kampanya Bilgileri:

{context}

Bu bilgiler kampanya detaylarından alınmıştır.""",
            "summary": """Kampanya Özeti:

{summary}

Detaylı bilgi için kampanya sayfasını ziyaret edebilirsiniz."""
        }
    
    def generate(self, query: str, retrieved_chunks: List[Dict]) -> str:
        """Generate response from retrieved chunks using OpenAI or template"""
        if not retrieved_chunks:
            return "Üzgünüm, bu soruya yanıt verebilecek kampanya bilgisi bulunamadı."
        
        context = self._build_context(retrieved_chunks)
        
        if self.use_openai and self.openai_client:
            return self._generate_with_openai(query, context, retrieved_chunks)
        else:
            return self.templates["default"].format(context=context)
    
    def _generate_with_openai(self, query: str, context: str, chunks: List[Dict] = None) -> str:
        """Generate response using OpenAI API with sophisticated prompt"""
        try:
            # Preprocess query to expand synonyms
            processed_query = self.preprocessor.preprocess_query(query)
            
            # Build synonym note if query was changed or variations found
            synonym_note = ""
            query_variations = self.preprocessor._generate_variations(query)
            processed_variations = self.preprocessor._generate_variations(processed_query)
            all_variations = query_variations | processed_variations
            
            context_lower = context.lower()
            found_variations = []
            matching_titles = []
            
            for variation in all_variations:
                if len(variation) > 2 and variation in context_lower:
                    found_variations.append(variation)
            
            if chunks:
                for chunk in chunks:
                    title = chunk.get("title", "")
                    chunk_text = chunk.get("text", "").lower()
                    title_lower = title.lower() if title else ""
                    
                    for variation in all_variations:
                        if len(variation) > 2:
                            if variation in chunk_text or variation in title_lower:
                                if title and title not in matching_titles:
                                    matching_titles.append(title)
                                break
            
            if found_variations or matching_titles or processed_query.lower() != query.lower():
                titles_note = ""
                if matching_titles:
                    titles_note = f" Örneğin bağlamda şu kampanyalar var: {', '.join(matching_titles[:3])}."
                
                variations_note = ""
                if found_variations:
                    variations_note = f" Bağlamda şu yazım şekilleri geçiyor: {', '.join(found_variations[:3])}."
                
                if processed_query.lower() != query.lower():
                    synonym_note = f"""

⚠️ KRİTİK TALİMAT - MUTLAKA UY: Kullanıcı "{query}" dedi. Bu terim "{processed_query}" ile TAMAMEN AYNI ANLAMA GELİR.{variations_note}{titles_note}

Eğer bağlamda "{processed_query}" veya benzer yazım şekillerindeki kampanyalar varsa, YANITINA "Evet, {processed_query} kampanyası hakkında bilgim var:" veya "{processed_query} kampanyası ile ilgili size bilgi verebilirim:" diye başla ve bağlamdaki ilgili kampanya bilgilerini detaylıca sun.

Eğer bağlamda "{processed_query}" veya benzer yazım şekillerindeki kampanyalar YOKSA, yanıt verme. Sadece "Üzgünüm, bu kampanya hakkında bilgim bulunmamaktadır." de.

ÖNEMLİ: Yanıtında kullanıcının sorusunu tekrar etme, sadece doğrudan cevap ver."""
                elif found_variations:
                    synonym_note = f"""

NOT: Kullanıcı "{query}" dedi. Bağlamda bu terimin farklı yazım şekilleri geçiyor: {', '.join(found_variations[:3])}. Bu yazım şekillerini eşleştir ve yanıtla."""
            
            system_prompt = """Sen uzman bir müşteri hizmetleri temsilcisisin. Kullanıcıların kampanya ve hizmetler hakkındaki sorularını yanıtlıyorsun.

GÖREV:
Verilen bağlam bilgilerine dayanarak kullanıcının sorusunu detaylı, net, yardımcı ve profesyonel bir şekilde Türkçe olarak yanıtla.

ÖNEMLİ KURALLAR:
1. SADECE bağlamda verilen bilgilere dayanarak yanıt ver - başka kaynaklardan bilgi ekleme
2. Bağlamda olmayan bilgiler için ASLA tahmin yapma, uydurma veya varsayımda bulunma
3. Yanıtını Türkçe, profesyonel, anlaşılır ve samimi bir dille yaz
4. Bağlamdaki bilgileri özetle, düzenle ve kullanıcının sorusuna odaklan
5. Kullanıcının sorusunu DOĞRUDAN ve EKSİKSİZ yanıtla
6. Eğer bağlamda soruya yanıt verecek ilgili kampanya YOKSA, sadece "Üzgünüm, bu kampanya hakkında bilgim bulunmamaktadır." de. Başka bir şey söyleme.
7. Yanıtında gereksiz tekrarlardan kaçın, öz ve net ol
8. Kampanya faydaları, koşullar ve detayları varsa mutlaka belirt
9. ÖNEMLİ - TERİM VARYASYONLARI: Kullanıcının sorusundaki terimlerin farklı yazım şekillerini (büyük/küçük harf, tire, alt çizgi, birleşik/ayrı yazım, Türkçe karakter varyasyonları) bağlamda ara. Örneğin: "Otoking", "autoking", "auto-king", "auto_king", "Auto King" aynı şeyi ifade edebilir. Bağlamda benzer terimler varsa bunları eşleştir ve yanıtla.
10. KRİTİK: Eğer kullanıcı bir kampanya adı söylediyse (örneğin "Otoking") ve bağlamda bu kampanyanın farklı yazım şekli varsa (örneğin "Auto King"), YANITINA "Evet, Auto King kampanyası hakkında bilgim var:" diye başla ve kampanya bilgilerini sun.
11. ASLA kullanıcının sorusunu veya sorgusunu yanıtında tekrar etme. Sadece doğrudan cevap ver.

YANIT FORMATI:
- Doğrudan soruya cevap ver, soruyu tekrar etme
- Gerekirse maddeler halinde düzenle
- Profesyonel ama samimi bir ton kullan"""
            
            user_prompt = f"""Aşağıdaki bağlam bilgilerine dayanarak kullanıcının sorusunu yanıtla.

BAĞLAM BİLGİLERİ:

{context}

KULLANICI SORUSU:

{query}{synonym_note}

YANIT:"""
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=800,
                top_p=0.9,
                frequency_penalty=0.3,
                presence_penalty=0.3
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            return self.templates["default"].format(context=context)
    
    def _build_context(self, chunks: List[Dict]) -> str:
        """Build context from retrieved chunks with detailed information"""
        context_parts = []
        
        for i, chunk in enumerate(chunks[:5], 1):
            title = chunk.get("title", "Bilinmeyen Kampanya")
            text = chunk.get("text", "")
            campaign_id = chunk.get("campaign_id", "")
            
            context_part = f"""
[{i}] Kampanya: {title}
Kampanya ID: {campaign_id}
İçerik: {text[:800]}
"""
            context_parts.append(context_part.strip())
        
        return "\n\n---\n\n".join(context_parts)
    
    def generate_summary(self, chunks: List[Dict]) -> str:
        """Generate summary from chunks"""
        if not chunks:
            return ""
        
        titles = set()
        for chunk in chunks:
            title = chunk.get("title", "")
            if title:
                titles.add(title)
        
        summary = f"İlgili {len(titles)} kampanya bulundu: " + ", ".join(list(titles)[:5])
        return summary

