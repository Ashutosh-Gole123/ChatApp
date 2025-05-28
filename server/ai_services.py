import requests
from transformers import pipeline
from dotenv import load_dotenv
import os
import time
import logging
from typing import Dict, List, Optional, Any
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")
HF_API_URL = "https://api-inference.huggingface.co/models/"

class AIService:
    def __init__(self):
        # Initialize local models with better error handling
        self.sentiment_analyzer = None
        self.summarizer = None
        self.translator = None
        
        # Try to load local models
        self._initialize_local_models()
        
        # Sentiment label mapping for Twitter RoBERTa model
        self.sentiment_labels = {
            "LABEL_0": "negative",
            "LABEL_1": "neutral", 
            "LABEL_2": "positive"
        }
        
        # Language codes for translation
        self.language_codes = {
            'spanish': 'es_XX',
            'french': 'fr_XX',
            'german': 'de_DE',
            'italian': 'it_IT',
            'portuguese': 'pt_XX',
            'chinese': 'zh_CN',
            'japanese': 'ja_XX',
            'korean': 'ko_KR',
            'arabic': 'ar_AR',
            'hindi': 'hi_IN'
        }

    def _initialize_local_models(self):
        """Initialize local transformer models"""
        try:
            logger.info("Loading sentiment analysis model...")
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis", 
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                device=-1  # Use CPU to avoid GPU issues
            )
            logger.info("Sentiment analyzer loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load sentiment analyzer: {e}")

        try:
            logger.info("Loading summarization model...")
            self.summarizer = pipeline(
                "summarization", 
                model="facebook/bart-large-cnn",
                device=-1
            )
            logger.info("Summarizer loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load summarizer: {e}")

    def call_hf_api(self, model: str, payload: Dict, retries: int = 3) -> Optional[Any]:
        """Enhanced HuggingFace API call with better error handling"""
        if not HF_API_KEY:
            logger.error("HuggingFace API key not found")
            return None
            
        headers = {"Authorization": f"Bearer {HF_API_KEY}"}
        
        for attempt in range(retries):
            try:
                response = requests.post(
                    HF_API_URL + model, 
                    headers=headers, 
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Handle model loading errors
                    if isinstance(result, dict) and "error" in result:
                        if "loading" in result["error"].lower():
                            logger.info(f"Model {model} is loading, waiting...")
                            time.sleep(20)  # Wait for model to load
                            continue
                        else:
                            logger.error(f"API Error: {result['error']}")
                            return None
                    
                    return result
                    
                elif response.status_code == 503:
                    logger.warning(f"Model {model} unavailable, retrying in {5 * (attempt + 1)} seconds...")
                    time.sleep(5 * (attempt + 1))
                    continue
                else:
                    logger.error(f"API request failed: {response.status_code} - {response.text}")
                    return None
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < retries - 1:
                    time.sleep(2)
                    continue
                    
        return None

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Improved sentiment analysis with proper label mapping"""
        if not text or not text.strip():
            return {"sentiment": "neutral", "confidence": 0.0, "error": "Empty text"}
        
        # Clean text
        text = text.strip()
        
        try:
            # Try local model first
            if self.sentiment_analyzer:
                result = self.sentiment_analyzer(text)[0]
                
                # Map label to readable sentiment
                raw_label = result["label"]
                sentiment = self.sentiment_labels.get(raw_label, raw_label.lower())
                
                return {
                    "sentiment": sentiment,
                    "confidence": round(result["score"], 3),
                    "raw_label": raw_label,
                    "method": "local"
                }
            
            # Fallback to API
            api_result = self.call_hf_api("cardiffnlp/twitter-roberta-base-sentiment-latest", {
                "inputs": text
            })
            
            if api_result and len(api_result) > 0:
                result = api_result[0]
                raw_label = result["label"]
                sentiment = self.sentiment_labels.get(raw_label, raw_label.lower())
                
                return {
                    "sentiment": sentiment,
                    "confidence": round(result["score"], 3),
                    "raw_label": raw_label,
                    "method": "api"
                }
                
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
        
        # Enhanced fallback based on simple keyword analysis
        positive_words = ['happy', 'good', 'great', 'excellent', 'love', 'like', 'amazing', 'wonderful', 'fantastic']
        negative_words = ['sad', 'bad', 'hate', 'terrible', 'awful', 'horrible', 'disgusting']
        
        text_lower = text.lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count > neg_count:
            return {"sentiment": "positive", "confidence": 0.6, "method": "keyword_fallback"}
        elif neg_count > pos_count:
            return {"sentiment": "negative", "confidence": 0.6, "method": "keyword_fallback"}
        else:
            return {"sentiment": "neutral", "confidence": 0.5, "method": "keyword_fallback"}

    def detect_language(self, text: str) -> Dict[str, Any]:
        """Detect language using HuggingFace API"""
        try:
            result = self.call_hf_api("papluca/xlm-roberta-base-language-detection", {
                "inputs": text
            })
            
            if result and len(result) > 0:
                return {
                    "language": result[0]["label"],
                    "confidence": round(result[0]["score"], 3)
                }
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
        
        return {"language": "en", "confidence": 0.5}

    def translate_message(self, text: str, target_language: str = "spanish") -> Dict[str, Any]:
        """Improved translation with language detection"""
        if not text or not text.strip():
            return {"error": "Empty text", "original": text}
        
        # Detect source language first
        lang_info = self.detect_language(text)
        detected_lang = lang_info.get("language", "en")
        
        # Don't translate if already in target language
        target_code = self.language_codes.get(target_language.lower(), "es_XX")
        
        if detected_lang == target_code.split('_')[0]:
            return {
                "original_text": text,
                "translated_text": text,
                "source_language": detected_lang,
                "target_language": target_language,
                "note": "Text already in target language"
            }
        
        try:
            # Use Google Translate model for better results
            result = self.call_hf_api("Helsinki-NLP/opus-mt-en-es", {
                "inputs": text
            })
            
            if result and len(result) > 0:
                translated = result[0].get("translation_text", text)
                return {
                    "original_text": text,
                    "translated_text": translated,
                    "source_language": detected_lang,
                    "target_language": target_language,
                    "confidence": lang_info.get("confidence", 0.5)
                }
                
        except Exception as e:
            logger.error(f"Translation failed: {e}")
        
        return {
            "error": "Translation failed",
            "original_text": text,
            "translated_text": text
        }

    def summarize_conversation(self, messages: List[Dict]) -> Dict[str, Any]:
        """Improved conversation summarization"""
        if not messages or len(messages) < 3:
            return {"error": "Not enough messages to summarize", "summary": ""}
        
        # Take last 20 messages and format them properly
        recent_messages = messages[-20:]
        
        # Create conversation text
        conversation = []
        for msg in recent_messages:
            sender = msg.get('sender_email', 'User').split('@')[0]  # Get username part
            message = msg.get('message', '')
            if message.strip():
                conversation.append(f"{sender}: {message}")
        
        text = "\n".join(conversation)
        
        # Check if text is long enough to summarize
        if len(text.split()) < 20:
            return {
                "summary": "Conversation too short to summarize effectively",
                "message_count": len(recent_messages),
                "word_count": len(text.split())
            }
        
        try:
            # Try local summarizer first
            if self.summarizer:
                # Truncate if too long
                if len(text) > 1000:
                    text = text[:1000] + "..."
                
                summary_result = self.summarizer(
                    text, 
                    max_length=100, 
                    min_length=30, 
                    do_sample=False
                )[0]
                
                return {
                    "summary": summary_result['summary_text'],
                    "message_count": len(recent_messages),
                    "method": "local"
                }
            
            # Fallback to API
            result = self.call_hf_api("facebook/bart-large-cnn", {
                "inputs": text[:1000],  # Limit input length
                "parameters": {
                    "max_length": 100,
                    "min_length": 30
                }
            })
            
            if result and len(result) > 0:
                return {
                    "summary": result[0].get("summary_text", "Summary unavailable"),
                    "message_count": len(recent_messages),
                    "method": "api"
                }
                
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
        
        return {
            "error": "Summarization failed",
            "summary": f"Recent conversation between {len(set(msg.get('sender_email', '') for msg in recent_messages))} participants with {len(recent_messages)} messages",
            "message_count": len(recent_messages)
        }

    def smart_reply_suggestions(self, message_history: List[Dict]) -> Dict[str, Any]:
        """Generate smart reply suggestions"""
        if not message_history:
            return {"suggestions": ["Hello!", "How are you?", "Nice to meet you!"]}
        
        # Get last few messages for context
        recent = message_history[-3:]
        context = " ".join([msg.get('message', '') for msg in recent])
        
        # Simple rule-based suggestions based on context
        suggestions = []
        
        context_lower = context.lower()
        
        # Greeting responses
        if any(word in context_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
            suggestions.extend(["Hello! How are you?", "Hi there!", "Nice to meet you!"])
        
        # Question responses
        elif '?' in context:
            suggestions.extend(["Let me think about that.", "That's a good question.", "I'm not sure, what do you think?"])
        
        # Positive responses
        elif any(word in context_lower for word in ['good', 'great', 'happy', 'excellent']):
            suggestions.extend(["That's wonderful!", "I'm glad to hear that!", "Sounds great!"])
        
        # Default suggestions
        else:
            suggestions.extend(["I understand.", "Tell me more about that.", "That's interesting."])
        
        # Limit to 3 suggestions
        return {"suggestions": suggestions[:3]}

    def enhance_message(self, text: str, style: str = "grammar") -> Dict[str, Any]:
        """Enhanced message improvement"""
        if not text or not text.strip():
            return {"enhanced": text, "error": "Empty text"}
        
        try:
            if style == "grammar":
                # Simple grammar corrections
                enhanced = self._basic_grammar_fix(text)
                return {
                    "original": text,
                    "enhanced": enhanced,
                    "style": style,
                    "method": "rule_based"
                }
            
            elif style == "professional":
                enhanced = self._make_professional(text)
                return {
                    "original": text,
                    "enhanced": enhanced,
                    "style": style,
                    "method": "rule_based"
                }
            
            else:  # casual
                enhanced = self._make_casual(text)
                return {
                    "original": text,
                    "enhanced": enhanced,
                    "style": style,
                    "method": "rule_based"
                }
                
        except Exception as e:
            logger.error(f"Message enhancement failed: {e}")
            return {"enhanced": text, "error": str(e)}

    def _basic_grammar_fix(self, text: str) -> str:
        """Basic grammar corrections"""
        # Capitalize first letter
        text = text.strip()
        if text:
            text = text[0].upper() + text[1:]
        
        # Fix common issues
        text = re.sub(r'\bi\b', 'I', text)  # Fix lowercase 'i'
        text = re.sub(r'\s+', ' ', text)    # Fix multiple spaces
        
        # Add period if missing
        if text and not text.endswith(('.', '!', '?')):
            text += '.'
        
        return text

    def _make_professional(self, text: str) -> str:
        """Make text more professional"""
        text = self._basic_grammar_fix(text)
        
        # Replace casual words
        replacements = {
            'hey': 'Hello',
            'yeah': 'Yes',
            'nope': 'No',
            'gonna': 'going to',
            'wanna': 'want to',
            'u': 'you',
            'ur': 'your'
        }
        
        for casual, formal in replacements.items():
            text = re.sub(r'\b' + casual + r'\b', formal, text, flags=re.IGNORECASE)
        
        return text

    def _make_casual(self, text: str) -> str:
        """Make text more casual"""
        # Add casual elements
        if not any(punct in text for punct in ['!', '?']):
            text = text.rstrip('.') + '!'
        
        return text

# Test the improved service
if __name__ == "__main__":
    ai_service = AIService()
    
    # Test messages
    test_messages = [
        "My name is Jyoti Sindkar. I am a Teacher.",
        "Happy to meet you",
        "I hate this product",
        "This is absolutely amazing!"
    ]
    
    print("=== TESTING IMPROVED AI SERVICE ===\n")
    
    for msg in test_messages:
        print(f"Message: '{msg}'")
        
        # Test sentiment
        sentiment = ai_service.analyze_sentiment(msg)
        print(f"Sentiment: {sentiment}")
        
        # Test language detection
        language = ai_service.detect_language(msg)
        print(f"Language: {language}")
        
        print("-" * 50)