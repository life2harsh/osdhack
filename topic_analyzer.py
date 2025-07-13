import json
import re
from typing import List, Dict, Optional, Tuple
from collections import deque, defaultdict
import time
import asyncio
import os
from mistralai import Mistral
import re
from typing import List, Dict, Optional, Tuple
from collections import deque, defaultdict
import time
import asyncio
import os
from openai import OpenAI

class TopicAnalyzer:
    def __init__(self, max_history_per_user=5, consecutive_threshold=4):
        """
        Initialize the topic analyzer with LLM support
        
        Args:
            max_history_per_user: Maximum messages to keep in history per user (reduced to 5 for context)
            consecutive_threshold: Number of consecutive messages on same topic to trigger room switch
        """
        self.message_history = defaultdict(lambda: deque(maxlen=max_history_per_user))
        self.consecutive_threshold = consecutive_threshold
        self.topic_confidence_threshold = 0.7
        
        # Predefined topics for fallback
        self.fallback_topics = {
            'python': ['python', 'django', 'flask', 'pandas', 'numpy', 'matplotlib', 'pip', 'conda'],
            'javascript': ['javascript', 'js', 'node', 'react', 'vue', 'angular', 'npm', 'webpack'],
            'ai': ['ai', 'artificial intelligence', 'machine learning', 'ml', 'neural network', 'deep learning', 'llm', 'gpt', 'chatgpt'],
            'games': ['game', 'gaming', 'unity', 'unreal', 'steam', 'nintendo', 'playstation', 'xbox'],
            'music': ['music', 'song', 'album', 'artist', 'spotify', 'guitar', 'piano', 'drums'],
            'programming': ['code', 'coding', 'programming', 'developer', 'software', 'algorithm', 'debug'],
            'web': ['html', 'css', 'website', 'web', 'frontend', 'backend', 'api', 'rest'],
            'database': ['database', 'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'orm'],
            'technology': ['tech', 'technology', 'computer', 'hardware', 'software', 'linux', 'windows', 'mac'],
            'sports': ['football', 'basketball', 'soccer', 'tennis', 'baseball', 'hockey', 'olympics'],
            'movies': ['movie', 'film', 'cinema', 'actor', 'director', 'netflix', 'disney', 'marvel'],
            'science': ['science', 'physics', 'chemistry', 'biology', 'research', 'experiment', 'theory']
        }
        
        # LLM API configuration (using Mistral)
        self.llm_model = "mistral-small-latest"  # Fast and efficient model
        self.mistral_api_key = None  # Will be loaded from environment or config
        self.llm_available = False
        self.client = None
        
    async def check_llm_availability(self):
        """Check if Mistral API is available"""
        try:
            # Load API key
            self.mistral_api_key = os.getenv('MISTRAL_API_KEY')
            if not self.mistral_api_key:
                try:
                    with open('secrets.txt', 'r') as f:
                        self.mistral_api_key = f.read().strip()
                except FileNotFoundError:
                    print("No Mistral API key found")
                    return False
            
            # Initialize client
            self.client = Mistral(api_key=self.mistral_api_key)
            
            # Test with a simple request (synchronous for simplicity)
            try:
                response = self.client.chat.complete(
                    model=self.llm_model,
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=5
                )
                
                if response and response.choices:
                    self.llm_available = True
                    print("Mistral API available")
                    return True
            except Exception as test_error:
                print(f"Mistral API test failed: {test_error}")
                        
        except Exception as e:
            print(f"Mistral API unavailable: {e}")
        
        self.llm_available = False
        return False
    
    async def detect_topic_with_llm(self, message: str, context_messages: Optional[List[str]] = None) -> Tuple[str, float]:
        """Detect topic using Mistral LLM with context"""
        if not self.llm_available or not self.client:
            return self.detect_topic_fallback(message)
        
        try:
            # Prepare context
            context = ""
            if context_messages:
                context = "Previous messages: " + " | ".join(context_messages[-2:]) + "\n\n"
            
            prompt = f"""{context}Classify this message into one topic: Python, JavaScript, AI, Games, Music, Programming, Web, Database, Technology, Sports, Movies, Science, General

Message: "{message}"

Respond with JSON: {{"topic": "TopicName", "confidence": 0.85}}"""

            # Use Mistral API (synchronous call, but we're in async context so it's fine)
            response = self.client.chat.complete(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.1
            )
            
            if response and response.choices and len(response.choices) > 0:
                message_content = response.choices[0].message.content
                response_text = ""
                
                # Handle Mistral content format
                if isinstance(message_content, list):
                    # Extract text from content chunks
                    for chunk in message_content:
                        if hasattr(chunk, 'text'):
                            response_text += getattr(chunk, 'text', '')
                        else:
                            response_text += str(chunk)
                elif isinstance(message_content, str):
                    response_text = message_content
                else:
                    response_text = str(message_content)
                
                response_text = response_text.strip()
                
                if response_text:
                    # Extract JSON from response
                    json_match = re.search(r'\{[^}]+\}', response_text)
                    if json_match:
                        json_data = json.loads(json_match.group())
                        topic = json_data.get('topic', 'General')
                        confidence = float(json_data.get('confidence', 0.5))
                        return topic, confidence
        
        except Exception as e:
            print(f"Mistral topic detection failed: {e}")
        
        return self.detect_topic_fallback(message)
    
    def detect_topic_fallback(self, message: str) -> Tuple[str, float]:
        """
        Fallback rule-based topic detection
        
        Returns:
            Tuple of (topic, confidence_score)
        """
        if not isinstance(message, str):
            return "General", 0.5
        
        msg = message.lower()
        msg_words = set(re.findall(r'\b\w+\b', msg))
        
        topic_scores = {}
        
        for topic, keywords in self.fallback_topics.items():
            matches = sum(1 for keyword in keywords if keyword in msg)
            if matches > 0:
                # Calculate confidence based on keyword matches and message length
                confidence = min(0.9, matches * 0.3 + (len([w for w in keywords if w in msg]) / len(msg_words)) * 0.5)
                topic_scores[topic] = confidence
        
        if topic_scores:
            best_topic = max(topic_scores.items(), key=lambda x: x[1])
            return best_topic[0].title(), best_topic[1]
        
        return "General", 0.4
    
    async def analyze_message(self, user_id: str, message: str) -> Dict:
        """
        Analyze a message and determine if user should be moved to a topic room
        
        Returns:
            Dict with topic, confidence, should_move, and consecutive_count
        """
        # Get user's message history (last 5 messages for context)
        user_history = list(self.message_history[user_id])
        context_messages = [msg['content'] for msg in user_history[-5:]]
        
        # Detect topic using LLM or fallback
        topic, confidence = await self.detect_topic_with_llm(message, context_messages)
        
        # Add message to history
        message_data = {
            'content': message,
            'topic': topic,
            'confidence': confidence,
            'timestamp': time.time()
        }
        self.message_history[user_id].append(message_data)
        
        # Check for consecutive messages on same topic
        consecutive_count = self._count_consecutive_topic_messages(user_id, topic)
        
        should_move = (
            consecutive_count >= self.consecutive_threshold and 
            confidence >= self.topic_confidence_threshold and
            topic != "General"
        )
        
        return {
            'topic': topic,
            'confidence': confidence,
            'should_move': should_move,
            'consecutive_count': consecutive_count,
            'room_name': f"topic:{topic}" if should_move else None
        }
    
    def _count_consecutive_topic_messages(self, user_id: str, topic: str) -> int:
        """Count consecutive messages on the same topic from the end of history"""
        history = list(self.message_history[user_id])
        if not history:
            return 0
        
        count = 0
        for message_data in reversed(history):
            if message_data['topic'] == topic:
                count += 1
            else:
                break
        
        return count
    
    def get_user_topic_stats(self, user_id: str) -> Dict:
        """Get topic statistics for a user"""
        history = list(self.message_history[user_id])
        if not history:
            return {}
        
        topic_counts = defaultdict(int)
        for msg in history:
            topic_counts[msg['topic']] += 1
        
        total_messages = len(history)
        topic_percentages = {
            topic: (count / total_messages) * 100 
            for topic, count in topic_counts.items()
        }
        
        return {
            'total_messages': total_messages,
            'topic_counts': dict(topic_counts),
            'topic_percentages': topic_percentages,
            'most_common_topic': max(topic_counts.items(), key=lambda x: x[1])[0] if topic_counts else None
        }
    
    def clear_user_history(self, user_id: str):
        """Clear message history for a user"""
        if user_id in self.message_history:
            del self.message_history[user_id]
    
    async def initialize(self):
        """Initialize the topic analyzer"""
        await self.check_llm_availability()
        print(f"Topic Analyzer initialized. OpenRouter API available: {self.llm_available}")
        if not self.llm_available:
            print("💡 To enable LLM-powered topic detection:")
            print("   1. Get a free API key from https://openrouter.ai/")
            print("   2. Set OPENROUTER_API_KEY environment variable OR")
            print("   3. Create 'openrouter_key.txt' file with your API key")
            print("   4. Using fallback rule-based detection for now")
