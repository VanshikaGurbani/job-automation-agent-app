"""
LLM Client for AI Models
Supports Google Gemini, Ollama, HuggingFace, and other LLM providers
"""
import requests
import json
import config


class LLMClient:
    """Unified client for LLM providers"""
    
    def __init__(self, provider=None, model=None):
        """
        Initialize LLM client
        
        Args:
            provider: LLM provider (gemini, ollama, huggingface)
            model: Model name to use
        """
        self.provider = provider or config.LLM_PROVIDER
        
        if self.provider == 'gemini':
            self.model = model or config.GEMINI_MODEL
            self.api_key = config.GEMINI_API_KEY
            self._init_gemini()
        else:
            self.model = model or config.OLLAMA_MODEL
            self.base_url = config.OLLAMA_BASE_URL
    
    def _init_gemini(self):
        """Initialize Gemini API client"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.genai = genai
            self.gemini_model = genai.GenerativeModel(self.model)
        except Exception as e:
            print(f"Error initializing Gemini: {e}")
            self.genai = None
        
    def generate(self, prompt, system_prompt="", temperature=0.7, max_tokens=8192):
        """
        Generate text using the LLM
        
        Args:
            prompt: User prompt
            system_prompt: System prompt for context
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate (8192 = max for Gemini 2.5 Flash)
        
        Returns:
            str: Generated text
        """
        if self.provider == 'gemini':
            return self._generate_gemini(prompt, system_prompt, temperature, max_tokens)
        elif self.provider == 'ollama':
            return self._generate_ollama(prompt, system_prompt, temperature)
        elif self.provider == 'huggingface':
            return self._generate_huggingface(prompt, system_prompt, temperature, max_tokens)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _generate_gemini(self, prompt, system_prompt, temperature, max_tokens):
        """Generate using Google Gemini API"""
        if not self.genai:
            raise Exception("Gemini not initialized. Check API key in config.")
        
        try:
            # Combine system and user prompts
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # Configure generation parameters
            generation_config = {
                'temperature': temperature,
                'max_output_tokens': max_tokens,  # Use what's requested
            }
            
            # CRITICAL: Explicitly disable safety filters for professional content
            # Without this, it uses strict defaults and blocks everything
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            
            # Generate content
            response = self.gemini_model.generate_content(
                full_prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            # Check if response was blocked
            if not response.candidates:
                print(f"  ⚠️ No candidates returned (likely blocked)")
                print(f"  Prompt length: {len(full_prompt)} chars")
                # Return empty instead of raising - let caller handle it
                return ""
            
            candidate = response.candidates[0]
            
            # Handle different finish reasons
            # finish_reason: 1=STOP (normal), 2=MAX_TOKENS (truncated), 3=SAFETY, 4=RECITATION, 5=OTHER
            finish_reason = candidate.finish_reason
            
            # Always try to get text first
            try:
                text = response.text.strip()
            except:
                text = ""
            
            if finish_reason == 3:  # SAFETY
                print(f"  ⚠️ Safety block (reason 3)")
                return ""
            elif finish_reason == 2:  # MAX_TOKENS
                # Return partial if we got something
                if text:
                    print(f"  ℹ️ Hit max tokens but got {len(text)} chars - using it")
                    return text
                else:
                    print(f"  ⚠️ Hit max tokens with no output - increase max_tokens!")
                    return ""
            elif finish_reason == 1:  # STOP (normal)
                return text
            else:
                # Unknown reason, try to return text
                if text:
                    return text
                return ""
            
        except Exception as e:
            raise Exception(f"Error generating with Gemini: {e}")
    
    def _generate_ollama(self, prompt, system_prompt, temperature):
        """Generate using Ollama"""
        url = f"{self.base_url}/api/generate"
        
        # Combine system and user prompts
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        payload = {
            "model": self.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()
            result = response.json()
            return result.get('response', '').strip()
        except requests.exceptions.ConnectionError:
            raise Exception(
                f"Could not connect to Ollama at {self.base_url}. "
                "Make sure Ollama is running (install from https://ollama.ai/ and run 'ollama serve')"
            )
        except Exception as e:
            raise Exception(f"Error generating with Ollama: {e}")
    
    def _generate_huggingface(self, prompt, system_prompt, temperature, max_tokens):
        """Generate using HuggingFace Inference API"""
        if not config.HUGGINGFACE_API_KEY:
            raise ValueError("HUGGINGFACE_API_KEY not set in config")
        
        url = f"https://api-inference.huggingface.co/models/{self.model}"
        headers = {"Authorization": f"Bearer {config.HUGGINGFACE_API_KEY}"}
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        payload = {
            "inputs": full_prompt,
            "parameters": {
                "temperature": temperature,
                "max_new_tokens": max_tokens
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('generated_text', '').strip()
            else:
                return str(result)
        except Exception as e:
            raise Exception(f"Error generating with HuggingFace: {e}")
    
    def chat(self, messages, temperature=0.7):
        """
        Chat completion (for models that support it)
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
        
        Returns:
            str: Generated response
        """
        if self.provider == 'ollama':
            return self._chat_ollama(messages, temperature)
        else:
            # Fallback: combine messages into a single prompt
            prompt = "\n\n".join([f"{m['role']}: {m['content']}" for m in messages])
            return self.generate(prompt, temperature=temperature)
    
    def _chat_ollama(self, messages, temperature):
        """Chat using Ollama's chat endpoint"""
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()
            result = response.json()
            return result.get('message', {}).get('content', '').strip()
        except requests.exceptions.ConnectionError:
            raise Exception(
                f"Could not connect to Ollama at {self.base_url}. "
                "Make sure Ollama is running and the model is downloaded.\n"
                f"Install from https://ollama.ai/ and run: ollama pull {self.model}"
            )
        except Exception as e:
            raise Exception(f"Error with Ollama chat: {e}")
    
    def is_available(self):
        """Check if the LLM service is available"""
        if self.provider == 'gemini':
            return self.genai is not None and bool(self.api_key)
        elif self.provider == 'ollama':
            try:
                response = requests.get(f"{self.base_url}/api/tags", timeout=5)
                return response.status_code == 200
            except:
                return False
        return True
    
    def list_models(self):
        """List available models"""
        if self.provider == 'gemini':
            return ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro']
        elif self.provider == 'ollama':
            try:
                response = requests.get(f"{self.base_url}/api/tags", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    return [model['name'] for model in data.get('models', [])]
            except:
                pass
        return []


# Test connection
def test_connection():
    """Test LLM connection"""
    client = LLMClient()
    
    print(f"Testing connection to {client.provider}...")
    print(f"Model: {client.model}")
    
    if client.provider == 'gemini':
        if not config.GEMINI_API_KEY:
            print("❌ GEMINI_API_KEY not set!")
            print("\nTo use Gemini:")
            print("1. Add GEMINI_API_KEY to .env file")
            print("2. Get API key from: https://makersuite.google.com/app/apikey")
            return False
        print(f"API Key: {config.GEMINI_API_KEY[:10]}...")
    elif client.provider == 'ollama':
        print(f"Base URL: {client.base_url}")
    
    if not client.is_available():
        print("❌ Service not available!")
        if client.provider == 'ollama':
            print("\nTo use Ollama:")
            print("1. Install from https://ollama.ai/")
            print("2. Run: ollama serve")
            print(f"3. Pull a model: ollama pull {client.model}")
        return False
    
    print("✓ Service is available!")
    
    models = client.list_models()
    if models:
        print(f"\nAvailable models: {', '.join(models)}")
    
    # Test generation
    try:
        print("\nTesting generation...")
        response = client.generate(
            "Say 'Hello, I am ready to help!' in one sentence.",
            system_prompt="You are a helpful assistant.",
            temperature=0.7
        )
        print(f"Response: {response}")
        print("\n✓ LLM is working correctly!")
        return True
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


if __name__ == "__main__":
    test_connection()

