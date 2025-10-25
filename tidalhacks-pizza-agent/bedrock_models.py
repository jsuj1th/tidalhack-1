# bedrock_models.py
"""
AWS Bedrock Model Configurations
Supports multiple model providers including Gemini and Claude
"""

import json
from typing import Dict, Any, Tuple

# Available Bedrock Models
BEDROCK_MODELS = {
    # Google Gemini Models
    "gemini-1.5-pro": {
        "model_id": "google.gemini-1.5-pro-v1:0",
        "provider": "google",
        "max_tokens": 8192,
        "supports_json": True,
        "cost_per_1k_input": 0.0025,
        "cost_per_1k_output": 0.0075,
        "description": "Google's most capable model with excellent reasoning"
    },
    "gemini-1.5-flash": {
        "model_id": "google.gemini-1.5-flash-v1:0", 
        "provider": "google",
        "max_tokens": 8192,
        "supports_json": True,
        "cost_per_1k_input": 0.00075,
        "cost_per_1k_output": 0.003,
        "description": "Faster, cost-effective Gemini model"
    },
    
    # Anthropic Claude Models (as alternatives)
    "claude-3-sonnet": {
        "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
        "provider": "anthropic",
        "max_tokens": 4096,
        "supports_json": True,
        "cost_per_1k_input": 0.003,
        "cost_per_1k_output": 0.015,
        "description": "Balanced performance and speed"
    },
    "claude-3-haiku": {
        "model_id": "anthropic.claude-3-haiku-20240307-v1:0",
        "provider": "anthropic", 
        "max_tokens": 4096,
        "supports_json": True,
        "cost_per_1k_input": 0.00025,
        "cost_per_1k_output": 0.00125,
        "description": "Fastest and most cost-effective Claude model"
    },
    
    # Amazon Titan Models
    "titan-text-express": {
        "model_id": "amazon.titan-text-express-v1",
        "provider": "amazon",
        "max_tokens": 8000,
        "supports_json": False,
        "cost_per_1k_input": 0.0008,
        "cost_per_1k_output": 0.0016,
        "description": "Amazon's text generation model"
    }
}

def get_model_config(model_name: str) -> Dict[str, Any]:
    """Get configuration for a specific model"""
    return BEDROCK_MODELS.get(model_name, BEDROCK_MODELS["gemini-1.5-pro"])

def get_model_by_id(model_id: str) -> Tuple[str, Dict[str, Any]]:
    """Get model name and config by model ID"""
    for name, config in BEDROCK_MODELS.items():
        if config["model_id"] == model_id:
            return name, config
    return "unknown", {"provider": "unknown", "max_tokens": 4096}

def format_request_body(model_id: str, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> Dict[str, Any]:
    """Format request body based on model provider"""
    _, config = get_model_by_id(model_id)
    provider = config.get("provider", "unknown")
    
    if provider == "google":
        # Gemini format
        return {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": min(max_tokens, config.get("max_tokens", 8192)),
                "temperature": temperature,
                "topP": 0.9,
                "topK": 40
            },
            "safetySettings": [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH", 
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
        }
    
    elif provider == "anthropic":
        # Claude format
        return {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": min(max_tokens, config.get("max_tokens", 4096)),
            "temperature": temperature,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
    
    elif provider == "amazon":
        # Titan format
        return {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": min(max_tokens, config.get("max_tokens", 8000)),
                "temperature": temperature,
                "topP": 0.9,
                "stopSequences": []
            }
        }
    
    else:
        # Generic format
        return {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

def parse_response(model_id: str, response_body: Dict[str, Any]) -> str:
    """Parse response based on model provider"""
    _, config = get_model_by_id(model_id)
    provider = config.get("provider", "unknown")
    
    if provider == "google":
        # Gemini response format
        if 'candidates' in response_body and len(response_body['candidates']) > 0:
            candidate = response_body['candidates'][0]
            if 'content' in candidate and 'parts' in candidate['content']:
                parts = candidate['content']['parts']
                if len(parts) > 0 and 'text' in parts[0]:
                    return parts[0]['text']
        
        # Fallback formats
        if 'outputs' in response_body:
            return response_body['outputs'][0].get('text', '')
        elif 'text' in response_body:
            return response_body['text']
        
        return str(response_body)
    
    elif provider == "anthropic":
        # Claude response format
        if 'content' in response_body and len(response_body['content']) > 0:
            return response_body['content'][0]['text']
        return str(response_body)
    
    elif provider == "amazon":
        # Titan response format
        if 'results' in response_body and len(response_body['results']) > 0:
            return response_body['results'][0]['outputText']
        return str(response_body)
    
    else:
        # Generic parsing
        if 'completion' in response_body:
            return response_body['completion']
        elif 'text' in response_body:
            return response_body['text']
        elif 'output' in response_body:
            return response_body['output']
        else:
            return str(response_body)

def estimate_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost for model usage"""
    _, config = get_model_by_id(model_id)
    
    input_cost = (input_tokens / 1000) * config.get("cost_per_1k_input", 0.001)
    output_cost = (output_tokens / 1000) * config.get("cost_per_1k_output", 0.001)
    
    return input_cost + output_cost

def get_recommended_model(use_case: str = "general") -> str:
    """Get recommended model for specific use case"""
    recommendations = {
        "general": "gemini-1.5-pro",
        "fast": "gemini-1.5-flash", 
        "cost_effective": "claude-3-haiku",
        "creative": "gemini-1.5-pro",
        "analytical": "claude-3-sonnet"
    }
    
    return recommendations.get(use_case, "gemini-1.5-pro")

def list_available_models() -> Dict[str, Dict[str, Any]]:
    """List all available models with their configurations"""
    return BEDROCK_MODELS

if __name__ == "__main__":
    print("🤖 AWS Bedrock Model Configurations")
    print("=" * 50)
    
    for name, config in BEDROCK_MODELS.items():
        print(f"\n{name}:")
        print(f"  Model ID: {config['model_id']}")
        print(f"  Provider: {config['provider']}")
        print(f"  Max Tokens: {config['max_tokens']}")
        print(f"  Cost (per 1K): ${config['cost_per_1k_input']:.4f} input, ${config['cost_per_1k_output']:.4f} output")
        print(f"  Description: {config['description']}")
    
    print(f"\n🎯 Recommended models:")
    print(f"  General use: {get_recommended_model('general')}")
    print(f"  Fast responses: {get_recommended_model('fast')}")
    print(f"  Cost effective: {get_recommended_model('cost_effective')}")
    print(f"  Creative tasks: {get_recommended_model('creative')}")