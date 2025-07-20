"""
Test utilities for Bhumi integration tests
"""

import os
import sys
import asyncio
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
import time
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from bhumi.base_client import BaseLLMClient, LLMConfig
from bhumi.utils import print_performance_status, check_performance_optimization

@dataclass
class TestResult:
    """Test result container"""
    provider: str
    test_name: str
    success: bool
    message: str
    duration: float
    details: Dict[str, Any]

@dataclass
class ProviderConfig:
    """Provider configuration for testing"""
    name: str
    env_var: str
    models: List[str]
    supports_streaming: bool
    max_tokens_required: bool

class TestEnvironment:
    """Manages test environment and API keys"""
    
    # Provider configurations
    PROVIDERS = {
        "openai": ProviderConfig(
            name="openai",
            env_var="OPENAI_API_KEY", 
            models=["openai/gpt-4o-mini", "openai/gpt-3.5-turbo"],
            supports_streaming=True,
            max_tokens_required=False
        ),
        "anthropic": ProviderConfig(
            name="anthropic",
            env_var="ANTHROPIC_API_KEY",
            models=["anthropic/claude-3-5-sonnet-20241022", "anthropic/claude-3-5-haiku-20241022"],
            supports_streaming=True,
            max_tokens_required=True
        ),
        "gemini": ProviderConfig(
            name="gemini", 
            env_var="GEMINI_API_KEY",
            models=["gemini/gemini-2.0-flash", "gemini/gemini-1.5-pro"],
            supports_streaming=True,
            max_tokens_required=False
        ),
        "groq": ProviderConfig(
            name="groq",
            env_var="GROQ_API_KEY", 
            models=["groq/moonshotai/kimi-k2-instruct", "groq/llama-3.1-8b-instant"],
            supports_streaming=True,
            max_tokens_required=False
        ),
        "openrouter": ProviderConfig(
            name="openrouter",
            env_var="OPENROUTER_API_KEY",
            models=["openrouter/moonshotai/kimi-k2-instruct", "openrouter/meta-llama/llama-3.1-8b-instruct"],
            supports_streaming=True, 
            max_tokens_required=False
        ),
        "sambanova": ProviderConfig(
            name="sambanova",
            env_var="SAMBANOVA_API_KEY",
            models=["sambanova/Meta-Llama-3.1-8B-Instruct", "sambanova/Meta-Llama-3.1-70B-Instruct"],
            supports_streaming=False,
            max_tokens_required=False
        )
    }
    
    @classmethod
    def load_env_file(cls) -> None:
        """Load environment variables from .env file if it exists"""
        # Look for .env file in current directory and parent directories
        current = Path.cwd()
        for path in [current, current.parent, current.parent.parent]:
            env_file = path / ".env"
            if env_file.exists():
                with open(env_file) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            os.environ[key.strip()] = value.strip()
                return
    
    @classmethod
    def get_api_key(cls, provider: str) -> Optional[str]:
        """Get API key for a provider"""
        if provider not in cls.PROVIDERS:
            return None
        
        env_var = cls.PROVIDERS[provider].env_var
        return os.environ.get(env_var)
    
    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of providers that have API keys available"""
        available = []
        for provider_name in cls.PROVIDERS:
            if cls.get_api_key(provider_name):
                available.append(provider_name)
        return available
    
    @classmethod
    def get_provider_config(cls, provider: str) -> Optional[ProviderConfig]:
        """Get configuration for a provider"""
        return cls.PROVIDERS.get(provider)

class IntegrationTestBase:
    """Base class for integration tests"""
    
    def __init__(self, provider: str):
        self.provider = provider
        self.config = TestEnvironment.get_provider_config(provider)
        self.api_key = TestEnvironment.get_api_key(provider)
        
        if not self.api_key:
            raise ValueError(f"No API key found for {provider}. Set {self.config.env_var} environment variable.")
        
        if not self.config:
            raise ValueError(f"Unknown provider: {provider}")
    
    def create_client(self, model: str, **kwargs) -> BaseLLMClient:
        """Create a client for testing"""
        config_kwargs = {
            "api_key": self.api_key,
            "model": model,
            "debug": False,
            **kwargs
        }
        
        # Add max_tokens if required by provider
        if self.config.max_tokens_required and "max_tokens" not in config_kwargs:
            config_kwargs["max_tokens"] = int(os.environ.get("TEST_MAX_TOKENS", "100"))
        
        config = LLMConfig(**config_kwargs)
        return BaseLLMClient(config, debug=False)
    
    async def test_simple_completion(self, model: str) -> TestResult:
        """Test simple completion"""
        start_time = time.time()
        
        try:
            client = self.create_client(model)
            
            messages = [
                {"role": "user", "content": f"Say 'Hello from {self.provider}!' and nothing else."}
            ]
            
            response = await client.completion(messages)
            
            duration = time.time() - start_time
            
            # Validate response
            if not response or not response.get("text"):
                return TestResult(
                    provider=self.provider,
                    test_name="simple_completion", 
                    success=False,
                    message="No response text received",
                    duration=duration,
                    details={"model": model, "response": response}
                )
            
            return TestResult(
                provider=self.provider,
                test_name="simple_completion",
                success=True,
                message=f"✅ Simple completion successful",
                duration=duration,
                details={
                    "model": model,
                    "response_length": len(str(response["text"])),
                    "has_usage": "usage" in response
                }
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                provider=self.provider,
                test_name="simple_completion",
                success=False,
                message=f"❌ Simple completion failed: {str(e)}",
                duration=duration,
                details={"model": model, "error": str(e)}
            )
    
    async def test_streaming_completion(self, model: str) -> TestResult:
        """Test streaming completion"""
        start_time = time.time()
        
        if not self.config.supports_streaming:
            return TestResult(
                provider=self.provider,
                test_name="streaming_completion",
                success=True,
                message=f"⚠️ Streaming not supported by {self.provider}",
                duration=0.0,
                details={"model": model, "skipped": True}
            )
        
        try:
            client = self.create_client(model)
            
            messages = [
                {"role": "user", "content": "Count from 1 to 3, one number per line."}
            ]
            
            chunks = []
            stream = await client.completion(messages, stream=True)
            
            async for chunk in stream:
                chunks.append(str(chunk))
            
            duration = time.time() - start_time
            
            if not chunks:
                return TestResult(
                    provider=self.provider,
                    test_name="streaming_completion",
                    success=False,
                    message="No streaming chunks received",
                    duration=duration,
                    details={"model": model, "chunks": chunks}
                )
            
            return TestResult(
                provider=self.provider,
                test_name="streaming_completion",
                success=True,
                message=f"✅ Streaming completion successful",
                duration=duration,
                details={
                    "model": model,
                    "chunks_received": len(chunks),
                    "total_content_length": sum(len(c) for c in chunks),
                    "first_chunk": chunks[0] if chunks else None
                }
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                provider=self.provider,
                test_name="streaming_completion",
                success=False,
                message=f"❌ Streaming completion failed: {str(e)}",
                duration=duration,
                details={"model": model, "error": str(e)}
            )
    
    async def test_map_elites_optimization(self, model: str) -> TestResult:
        """Test MAP-Elites optimization"""
        start_time = time.time()
        
        try:
            client = self.create_client(model)
            
            # Get initial buffer state
            initial_buffer = client.buffer_strategy.get_size()
            perf_info = client.buffer_strategy.get_performance_info()
            
            # Test that optimization is working
            optimization_status = check_performance_optimization()
            
            duration = time.time() - start_time
            
            return TestResult(
                provider=self.provider,
                test_name="map_elites_optimization",
                success=optimization_status["optimized"],
                message=f"✅ MAP-Elites optimization active" if optimization_status["optimized"] else "❌ MAP-Elites optimization not active",
                duration=duration,
                details={
                    "model": model,
                    "initial_buffer_size": initial_buffer,
                    "total_entries": perf_info["total_entries"],
                    "coverage": perf_info["optimization_coverage"],
                    "optimization_status": optimization_status
                }
            )
            
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                provider=self.provider,
                test_name="map_elites_optimization",
                success=False,
                message=f"❌ MAP-Elites test failed: {str(e)}",
                duration=duration,
                details={"model": model, "error": str(e)}
            )

async def run_comprehensive_test(provider: str) -> List[TestResult]:
    """Run comprehensive test suite for a provider"""
    try:
        test_base = IntegrationTestBase(provider)
        config = TestEnvironment.get_provider_config(provider)
        
        results = []
        
        # Test each model
        for model in config.models:
            print(f"🧪 Testing {provider} with model {model}")
            
            # Run all tests for this model
            simple_result = await test_base.test_simple_completion(model)
            results.append(simple_result)
            
            streaming_result = await test_base.test_streaming_completion(model)
            results.append(streaming_result)
            
            optimization_result = await test_base.test_map_elites_optimization(model)
            results.append(optimization_result)
            
            # Short delay between tests
            await asyncio.sleep(1)
        
        return results
        
    except Exception as e:
        return [TestResult(
            provider=provider,
            test_name="provider_setup",
            success=False,
            message=f"❌ Provider setup failed: {str(e)}",
            duration=0.0,
            details={"error": str(e)}
        )] 