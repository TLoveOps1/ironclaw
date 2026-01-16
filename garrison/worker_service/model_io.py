import os
import time
from typing import Dict, Any, Tuple
from openai import OpenAI

def call_model(config: Dict[str, Any], prompt: str) -> Tuple[str, Dict[str, Any], float]:
    """
    Calls the model based on resolved config.
    Returns: (response_text, usage_dict, latency_ms)
    """
    api_key = os.environ.get("IO_INTELLIGENCE_API_KEY") or os.environ.get("OPENAI_API_KEY") or "sk-placeholder"
    base_url = os.environ.get("IO_INTELLIGENCE_BASE_URL") or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
    
    client = OpenAI(api_key=api_key, base_url=base_url)
    
    model = config.get("model")
    temp = config.get("temperature", 0.2)
    max_tokens = config.get("max_tokens", 800)
    
    start_time = time.time()
    
    # Simple retry logic as requested
    max_retries = config.get("retries", 3)
    last_error = None
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temp,
                max_tokens=max_tokens,
                timeout=config.get("timeout_seconds", 60)
            )
            
            latency = (time.time() - start_time) * 1000
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            return response.choices[0].message.content, usage, latency
            
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt) # Exponential backoff
            
    raise last_error
