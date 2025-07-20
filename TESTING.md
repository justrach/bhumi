# 🧪 Bhumi Testing Guide

## Overview

Bhumi includes comprehensive integration tests for all supported providers with optimized MAP-Elites system validation. The testing infrastructure ensures reliable performance across multiple LLM providers and validates the enhanced buffer optimization.

## 🚀 **New Integration Test System**

### **Environment Setup**

1. **Copy environment template:**
   ```bash
   cp env.example .env
   ```

2. **Add your API keys to `.env`:**
   ```bash
   # Required API Keys
   OPENAI_API_KEY=sk-your-openai-key
   ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
   GEMINI_API_KEY=your-gemini-key
   GROQ_API_KEY=gsk_your-groq-key
   OPENROUTER_API_KEY=sk-or-v1-your-openrouter-key
   SAMBANOVA_API_KEY=your-sambanova-key
   ```

3. **Quick setup and demo:**
   ```bash
   python test_setup.py
   ```

### **Local Testing**

**Run all available providers:**
```bash
cd tests/integration
python test_all_providers.py
```

**Test specific provider (from root):**
```bash
python -c "
import asyncio, sys
sys.path.append('tests')
from test_utils import run_comprehensive_test
results = asyncio.run(run_comprehensive_test('anthropic'))
print(f'Results: {sum(r.success for r in results)}/{len(results)} passed')
"
```

### **Test Coverage**

Each provider is tested for:
- ✅ **Simple Completion**: Basic request/response functionality  
- ✅ **Streaming Completion**: Real-time streaming responses
- ✅ **MAP-Elites Optimization**: Buffer optimization and performance validation
- ✅ **Error Handling**: Graceful failure and recovery
- ✅ **Performance Metrics**: Response times and throughput

## 🔄 **GitHub Actions Workflow**

### **Automatic Testing**

The integration tests run automatically on:
- **Push to main/develop branches**
- **Pull requests**
- **Daily schedule** (6 AM UTC)
- **Manual trigger** via GitHub UI

### **Workflow Features**

**Multi-Python Testing:**
- Tests on Python 3.9, 3.10, 3.11, 3.12
- Comprehensive provider coverage
- Performance benchmarking

**Test Reports:**
- JSON test results with detailed metrics
- GitHub step summaries with pass/fail status  
- Artifact uploads for debugging
- Performance benchmarks for optimization validation

**Smart Provider Detection:**
- Only tests providers with available API keys
- Graceful handling of missing credentials
- Detailed failure reporting

### **Setting up GitHub Secrets**

Add these secrets to your GitHub repository:

```bash
# Repository Settings > Secrets and Variables > Actions

OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key  
GEMINI_API_KEY=your-gemini-key
GROQ_API_KEY=gsk_your-groq-key
OPENROUTER_API_KEY=sk-or-v1-your-openrouter-key
SAMBANOVA_API_KEY=your-sambanova-key
```

### **Manual Workflow Trigger**

You can run tests for specific providers:

1. Go to **Actions** tab in GitHub
2. Select **"🚀 Bhumi Integration Tests"**  
3. Click **"Run workflow"**
4. Choose providers: `anthropic,openai` or `all`

## 📊 **Test Results and Reporting**

### **JSON Report Format**

```json
{
  "timestamp": 1674123456.789,
  "duration": 45.67,
  "providers_tested": 3,
  "total_tests": 18,
  "passed_tests": 16,
  "optimization_active": true,
  "providers": {
    "anthropic": {
      "total": 6,
      "passed": 6,
      "tests": [
        {
          "name": "simple_completion",
          "success": true,
          "duration": 2.34,
          "model": "anthropic/claude-3-5-sonnet-20241022"
        }
      ]
    }
  }
}
```

### **Performance Validation**

Tests verify:
- ⚡ **MAP-Elites Loading**: 3x faster with Satya + orjson
- 📊 **Archive Coverage**: Optimization coverage percentage  
- 🧠 **Buffer Adjustment**: Dynamic buffer sizing based on usage
- 🔄 **Streaming Performance**: Real-time chunk processing
- 📈 **Response Times**: Latency and throughput metrics

## 🛠 **Provider-Specific Testing**

### **OpenAI**
```bash
# Models tested
openai/gpt-4o-mini
openai/gpt-3.5-turbo
# Features: Streaming ✅, Function calling ✅
```

### **Anthropic** 
```bash
# Models tested  
anthropic/claude-3-5-sonnet-20241022
anthropic/claude-3-5-haiku-20241022
# Features: Streaming ✅, max_tokens required ✅
```

### **Groq**
```bash
# Models tested
groq/moonshotai/kimi-k2-instruct  
groq/llama-3.1-8b-instant
# Features: Streaming ✅, Gateway provider parsing ✅
```

### **OpenRouter**
```bash  
# Models tested
openrouter/moonshotai/kimi-k2-instruct
openrouter/meta-llama/llama-3.1-8b-instruct  
# Features: Streaming ✅, Gateway provider parsing ✅
```

### **Gemini**
```bash
# Models tested
gemini/gemini-2.0-flash
gemini/gemini-1.5-pro
# Features: Streaming ✅, Google AI integration ✅
```

### **SambaNova**
```bash
# Models tested  
sambanova/Meta-Llama-3.1-8B-Instruct
sambanova/Meta-Llama-3.1-70B-Instruct
# Features: Basic completion ✅, Streaming ❌
```

## 🐛 **Debugging Failed Tests**

### **Common Issues**

1. **API Key Problems:**
   ```bash
   # Check .env file
   cat .env | grep API_KEY
   
   # Verify key format
   echo $ANTHROPIC_API_KEY | cut -c1-20
   ```

2. **Network Issues:**
   ```bash
   # Test connectivity
   curl -s https://api.anthropic.com/v1/messages -I
   ```

3. **Model Availability:**
   ```bash
   # Check if model is accessible
   python -c "
   from bhumi.base_client import BaseLLMClient, LLMConfig
   config = LLMConfig(api_key='test', model='anthropic/claude-3-5-sonnet-20241022')
   print('Model configuration valid')
   "
   ```

### **Viewing Test Logs**

**Local:**
```bash
cd tests/integration  
python test_all_providers.py > test.log 2>&1
cat test.log
```

**GitHub Actions:**
1. Go to **Actions** tab
2. Select failed workflow run
3. Click on **"🧪 Integration Tests"** job  
4. Expand **"Run Integration Tests"** step
5. Download test artifacts for detailed analysis

## 💡 **Best Practices**

1. **Always test locally** before pushing changes
2. **Add new providers** to `test_utils.py` configuration  
3. **Update models list** when new models are available
4. **Set appropriate timeouts** for slow providers
5. **Monitor rate limits** and add delays if needed
6. **Document provider-specific requirements** (like max_tokens)

## 🔧 **Extending Tests**

### **Adding New Provider**

1. **Update `test_utils.py`:**
   ```python
   "newprovider": ProviderConfig(
       name="newprovider",
       env_var="NEWPROVIDER_API_KEY",
       models=["newprovider/model1", "newprovider/model2"],
       supports_streaming=True,
       max_tokens_required=False
   )
   ```

2. **Add to environment template:**
   ```bash
   echo "NEWPROVIDER_API_KEY=your-key-here" >> env.example
   ```

3. **Update GitHub workflow:**
   ```yaml
   env:
     NEWPROVIDER_API_KEY: ${{ secrets.NEWPROVIDER_API_KEY }}
   ```

### **Adding New Test Types**

Extend `IntegrationTestBase` class:
```python
async def test_custom_feature(self, model: str) -> TestResult:
    """Test custom provider feature"""
    # Implementation here
    pass
```

## 📈 **Performance Monitoring**

The integration tests validate that the optimized MAP-Elites system provides:
- **3x faster archive loading** with Satya + orjson
- **Dynamic buffer optimization** based on usage patterns  
- **100% archive coverage** with optimized configurations
- **Robust error handling** with intelligent fallbacks
- **Real-time performance** monitoring and adjustment

**Success Criteria:**
- ✅ All provider tests pass
- ✅ MAP-Elites optimization active  
- ✅ Archive loading < 10ms
- ✅ Streaming responses working
- ✅ Buffer adjustment functional

This comprehensive testing ensures Bhumi delivers **blazing-fast, reliable AI inference** across all supported providers! 🚀 