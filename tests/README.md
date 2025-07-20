# 🧪 Bhumi Tests

## Directory Structure

```
tests/
├── README.md                    # This file
├── test_utils.py               # Test utilities and base classes
├── integration/                # Integration tests
│   ├── test_all_providers.py  # Main integration test runner  
│   ├── test_groq_kimi.py      # Groq Kimi-specific tests
│   └── test_openrouter_kimi.py # OpenRouter Kimi-specific tests  
└── unit/                       # Unit tests (for future expansion)
```

## Quick Start

### 1. **Setup Environment**
```bash
# From project root
cp env.example .env
# Add your API keys to .env
```

### 2. **Run Setup Script**
```bash
python test_setup.py
```

### 3. **Run Full Integration Tests**
```bash
cd tests/integration
python test_all_providers.py
```

## Test Categories

### **Integration Tests** (`integration/`)
- **`test_all_providers.py`**: Comprehensive test runner for all providers
- **`test_groq_kimi.py`**: Focused tests for Groq Kimi model
- **`test_openrouter_kimi.py`**: Focused tests for OpenRouter Kimi model

### **Test Utilities** (`test_utils.py`)
- Provider configuration management
- Environment variable handling  
- Base test classes and utilities
- Test result reporting

## Features

✅ **Multi-Provider Testing**: OpenAI, Anthropic, Gemini, Groq, OpenRouter, SambaNova  
✅ **Streaming Validation**: Real-time streaming response testing  
✅ **MAP-Elites Optimization**: Performance optimization validation  
✅ **Error Handling**: Graceful failure and recovery testing  
✅ **GitHub Integration**: Automated CI/CD testing  
✅ **JSON Reporting**: Detailed test results for analysis  

## Environment Variables

Required for testing (add to `.env`):
```bash
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key  
GEMINI_API_KEY=your-gemini-key
GROQ_API_KEY=gsk_your-groq-key
OPENROUTER_API_KEY=sk-or-v1-your-openrouter-key
SAMBANOVA_API_KEY=your-sambanova-key
```

## Adding New Tests

### **New Provider**
1. Update `test_utils.py` with provider configuration
2. Add environment variable to templates
3. Test locally and update GitHub workflow

### **New Test Type**
1. Extend `IntegrationTestBase` class in `test_utils.py`
2. Add test method following the pattern:
   ```python
   async def test_new_feature(self, model: str) -> TestResult:
       # Implementation
       pass
   ```

## GitHub Actions

Tests automatically run on:
- Push to main/develop
- Pull requests  
- Daily schedule (6 AM UTC)
- Manual trigger

Results available in GitHub Actions with detailed reports and artifacts.

For more information, see [TESTING.md](../TESTING.md). 