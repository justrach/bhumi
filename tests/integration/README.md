# Comprehensive Provider Integration Tests

This directory contains comprehensive integration tests for all supported LLM providers in Bhumi. Each provider has its own test suite covering streaming, tool use, and structured outputs.

## Supported Providers

- **OpenAI** (`test_openai_comprehensive.py`) - GPT models with Responses API support
- **Anthropic** (`test_anthropic_comprehensive.py`) - Claude models  
- **Gemini** (`test_gemini_comprehensive.py`) - Google Gemini models
- **Cerebras** (`test_cerebras_comprehensive.py`) - Cerebras inference models
- **Groq** (`test_groq_comprehensive.py`) - Groq inference models

## Test Coverage

Each provider test suite covers:

### 🔧 **Basic Functionality**
- Chat Completions API
- System message handling
- Multi-turn conversations
- Math and reasoning tasks

### 🌊 **Streaming**
- Basic streaming responses
- Streaming with system messages
- Creative and analytical tasks
- Chunk counting and accumulation

### 🛠️ **Tool Use (Function Calling)**
- Simple function calling
- Calculator tools
- Weather/data lookup tools
- Multiple tools working together
- Tool result handling

### 📊 **Structured Outputs**
- JSON output via prompt engineering
- Satya model integration (if available)
- Data extraction tasks
- List and object generation
- Schema validation

### 🧪 **Edge Cases**
- Empty message handling
- Long conversations
- Special characters
- Error conditions
- Performance testing

## Setup

### 1. Install Dependencies

```bash
pip install pytest pytest-asyncio python-dotenv
# Optional: pip install pytest-cov for coverage
```

### 2. Set API Keys

Create a `.env` file in the project root:

```bash
# Required for each provider you want to test
export OPENAI_API_KEY=your_openai_key
export ANTHROPIC_API_KEY=your_anthropic_key  
export GEMINI_API_KEY=your_gemini_key
export CEREBRAS_API_KEY=your_cerebras_key
export GROQ_API_KEY=your_groq_key
export MISTRAL_API_KEY=your_mistral_key
```

### 3. Optional: Install Satya

For structured output tests:

```bash
pip install satya
```

## Running Tests

### Run All Available Providers

```bash
# Run all providers with available API keys
python tests/integration/run_all_providers.py

# Verbose output
python tests/integration/run_all_providers.py -v

# Stop on first failure
python tests/integration/run_all_providers.py -x

# Use simple tests for problematic providers (recommended for Cerebras)
python tests/integration/run_all_providers.py --simple

# Skip tool calling entirely (fastest for Cerebras)
python tests/integration/run_all_providers.py --no-tools
```

### Run Specific Providers

```bash
# Test only OpenAI
python tests/integration/run_all_providers.py openai

# Test OpenAI and Anthropic
python tests/integration/run_all_providers.py openai anthropic

# Test with verbose output
python tests/integration/run_all_providers.py openai -v
```

### Run Individual Provider Tests

```bash
# OpenAI tests
pytest tests/integration/test_openai_comprehensive.py -v

# Anthropic tests  
pytest tests/integration/test_anthropic_comprehensive.py -v

# Gemini tests
pytest tests/integration/test_gemini_comprehensive.py -v

# Cerebras tests (multiple options)
pytest tests/integration/test_cerebras_comprehensive.py -v  # Full tests (may hang on tools)
pytest tests/integration/test_cerebras_simple.py -v        # Simple tests with timeouts
pytest tests/integration/test_cerebras_no_tools.py -v      # No tool calling (fastest)

# Groq tests
pytest tests/integration/test_groq_comprehensive.py -v

# Mistral tests
pytest tests/integration/test_mistral_comprehensive.py -v
```

### Run Specific Test Classes

```bash
# Only streaming tests for OpenAI
pytest tests/integration/test_openai_comprehensive.py::TestOpenAIStreaming -v

# Only tool tests for Anthropic
pytest tests/integration/test_anthropic_comprehensive.py::TestAnthropicTools -v

# Only structured output tests for Gemini
pytest tests/integration/test_gemini_comprehensive.py::TestGeminiStructuredOutputs -v
```

### Check API Key Status

```bash
python tests/integration/run_all_providers.py --check-keys
```

## Test Results Interpretation

### ✅ **Expected to Pass**
- Basic functionality (all providers)
- Streaming (most providers, some prompts may vary)
- Tool use (all providers with tool registry)
- Structured outputs via prompt engineering

### ⚠️ **May Vary by Provider**
- **Streaming performance**: Some providers stream better than others
- **Tool calling format**: Different providers may have different tool calling patterns
- **Structured output quality**: Varies by model capability
- **Response times**: Varies significantly by provider

### ❌ **Known Issues**
- **OpenAI Responses API**: Currently uses fallback to Chat Completions
- **Complex streaming prompts**: Some prompts may return 0 chunks
- **Anthropic structured outputs**: May need different approach than OpenAI
- **API rate limits**: Tests may fail due to rate limiting

## Provider-Specific Notes

### OpenAI
- ✅ **Responses API**: Supported with `input=` and `instructions=` parameters
- ✅ **Streaming**: Excellent support
- ✅ **Tools**: Full function calling support
- ✅ **Structured outputs**: Native support + Satya integration

### Anthropic
- ✅ **Chat Completions**: Full support
- ✅ **Streaming**: Good support
- ✅ **Tools**: Function calling via tool registry
- ⚠️ **Structured outputs**: Uses prompt engineering approach

### Gemini
- ✅ **Chat Completions**: Full support via OpenAI-compatible endpoint
- ✅ **Streaming**: Good support
- ✅ **Tools**: Function calling support
- ⚠️ **Structured outputs**: Uses prompt engineering approach

### Cerebras
- ✅ **Chat Completions**: Full support
- ✅ **Streaming**: Good support for creative tasks
- ✅ **Tools**: Function calling supported with `llama-4-scout-17b-16e-instruct` model (requires `"strict": true` in tool schema)
- ⚠️ **Structured outputs**: Uses prompt engineering approach

**Important**: Cerebras requires specific models for tool calling:
- ✅ `llama-4-scout-17b-16e-instruct` - Supports tool calling
- ❌ `llama3.1-8b` - Does NOT support tool calling

The tests automatically use the correct model (`llama-4-scout-17b-16e-instruct`) for tool testing.

### Mistral AI
- ✅ **Chat Completions**: Full support via OpenAI-compatible API
- ✅ **Streaming**: Excellent support
- ✅ **Tools**: Function calling support with standard OpenAI format
- ✅ **Vision**: Image analysis with Pixtral models (e.g., `pixtral-12b-2409`)
- ⚠️ **Structured outputs**: Uses prompt engineering approach

**Models**: `mistral-small-latest`, `mistral-medium-latest`, `mistral-large-latest`, `pixtral-12b-2409` (vision)

### Groq
- ✅ **Chat Completions**: Full support
- ✅ **Streaming**: Excellent speed
- ✅ **Tools**: Function calling support
- ⚠️ **Structured outputs**: Uses prompt engineering approach

## Troubleshooting

### Common Issues

1. **Missing API Keys**
   ```bash
   # Check which keys are available
   python tests/integration/run_all_providers.py --check-keys
   ```

2. **Rate Limiting**
   ```bash
   # Run tests with delays
   pytest tests/integration/test_openai_comprehensive.py -v -s --tb=short
   ```

3. **Streaming Issues**
   - Some prompts work better for streaming than others
   - Try simpler, more direct prompts
   - Check provider-specific streaming capabilities

4. **Tool Calling Issues**
   - Ensure tools are properly registered
   - Check tool parameter schemas
   - Verify function implementations
   - **For Cerebras**: Use simple tests (`--simple` flag) if tool calling hangs

5. **Cerebras-Specific Issues**
   - Tool calling may timeout or hang
   - **Multiple solutions available**:
     - Use simple tests: `pytest tests/integration/test_cerebras_simple.py -v`
     - Skip tools entirely: `pytest tests/integration/test_cerebras_no_tools.py -v`
     - Use flags: `python tests/integration/run_all_providers.py cerebras --no-tools`

6. **Structured Output Issues**
   - Try prompt engineering approach first
   - Check if Satya is installed for advanced structured outputs
   - Verify JSON parsing logic

### Debug Mode

Enable debug mode for detailed logging:

```python
config = LLMConfig(
    api_key=api_key,
    model="provider/model",
    debug=True  # Enable debug logging
)
```

## Contributing

When adding new providers or tests:

1. Follow the existing test structure
2. Include all test categories (basic, streaming, tools, structured outputs)
3. Add provider-specific edge cases
4. Update this README with provider notes
5. Test with real API keys before submitting

## Performance Benchmarking

For performance testing:

```bash
# Run with timing
pytest tests/integration/test_openai_comprehensive.py::TestOpenAIStreaming -v --durations=10

# Run with coverage
pytest tests/integration/ --cov=bhumi --cov-report=html
```

This will help identify slow tests and coverage gaps.
