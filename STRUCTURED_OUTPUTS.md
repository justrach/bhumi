# Structured Outputs in Bhumi

Bhumi now supports structured outputs following OpenAI and Anthropic patterns for better compatibility and developer experience. **Now with Satya high-performance validation support!**

## Quick Start

```python
from bhumi import BaseLLMClient, LLMConfig, ResponseFormat
from pydantic import BaseModel, Field

class UserProfile(BaseModel):
    name: str = Field(description="User's full name")
    age: int = Field(description="User's age")
    email: str = Field(description="User's email address")

# Create client
client = BaseLLMClient(LLMConfig(
    api_key="your-api-key",
    model="openai/gpt-4o-mini"
))

# Use the new parse() method (similar to OpenAI)
completion = await client.parse(
    messages=[
        {"role": "user", "content": "Create a user profile for John, age 30"}
    ],
    response_format=UserProfile  # Pass Pydantic model directly
)

# Access parsed data directly
user = completion.parsed
print(f"Name: {user.name}, Age: {user.age}")
```

## High-Performance Satya Support

For production workloads requiring maximum performance, use Satya models:

```python
from satya import Model, Field

class UserProfile(Model):
    name: str = Field(description="User's full name")
    age: int = Field(description="User's age") 
    email: str = Field(description="User's email address")

# Same API - just pass Satya model instead!
completion = await client.parse(
    messages=[
        {"role": "user", "content": "Create a user profile for John, age 30"}
    ],
    response_format=UserProfile  # Pass Satya model directly
)

user = completion.parsed  # High-performance validation!
```

## Key Features

### 1. OpenAI-Compatible `parse()` Method

The new `client.parse()` method works similarly to OpenAI's `client.chat.completions.parse()`:

- **Automatic JSON schema generation** from Pydantic and Satya models
- **Built-in response validation** and parsing
- **Error handling** for length limits, content filtering, and refusals
- **Structured response objects** with typed access to parsed data

### 2. Response Format Creation

Multiple ways to create response formats:

```python
from bhumi import ResponseFormat

# From Pydantic model (recommended)
format1 = ResponseFormat.from_model(UserProfile, name="user_profile")

# From Satya model (high-performance)
format2 = ResponseFormat.from_model(SatyaUserProfile, name="user_profile")

# JSON object mode
format3 = ResponseFormat.json_object()

# Custom JSON schema
format4 = ResponseFormat.json_schema(
    schema={"type": "object", "properties": {"name": {"type": "string"}}},
    name="custom_schema"
)
```

### 3. Tool Creation Helpers

Create tools for both OpenAI and Anthropic formats:

```python
from bhumi import pydantic_function_tool, pydantic_tool_schema

# OpenAI-style function tool (works with both Pydantic and Satya)
openai_tool = pydantic_function_tool(UserProfile, name="create_user")

# Anthropic-style tool schema (works with both Pydantic and Satya)
anthropic_tool = pydantic_tool_schema(UserProfile)
```

### 4. Error Handling

Built-in exception types for common issues:

```python
from bhumi import LengthFinishReasonError, ContentFilterFinishReasonError

try:
    completion = await client.parse(messages=messages, response_format=UserProfile)
except LengthFinishReasonError:
    print("Response was cut off due to length limits")
except ContentFilterFinishReasonError:
    print("Response was filtered by content policy")
```

## Structured Response Objects

The `ParsedChatCompletion` response provides:

```python
completion = await client.parse(...)

# Access parsed data
user = completion.parsed  # Your Pydantic/Satya model instance

# Access raw response data
completion.id           # Response ID
completion.model        # Model used
completion.choices[0]   # First choice
completion.usage        # Token usage info

# Handle parsing failures gracefully
if completion.parsed is None:
    if completion.choices[0].message.refusal:
        print("Model refused to answer")
    else:
        print("Failed to parse response")
```

## Model Support

Bhumi supports both Pydantic and Satya models for maximum flexibility:

### Pydantic Models (Standard)
- Full Pydantic ecosystem compatibility
- Rich validation features and error messages
- Type coercion and defaults
- Complex nested structures

### Satya Models (High-Performance)
- **2-7x faster** validation than Pydantic
- Rust-powered core for production workloads
- Batch processing with configurable batch sizes
- Stream processing for unlimited datasets
- Memory-efficient design

## Performance Comparison

| Feature | Pydantic | Satya |
|---------|----------|-------|
| **Performance** | Standard | **2-7x faster** |
| **Memory Usage** | Standard | **More efficient** |
| **Batch Processing** | Limited | **Optimized** |
| **Stream Processing** | Limited | **Unlimited datasets** |
| **Type Coercion** | Rich | Focused |
| **Ecosystem** | Large | Growing |

## Migration from Old Approach

### Old Way (Deprecated)
```python
# Old approach - now deprecated
client.set_structured_output(UserProfile)
response = await client.completion([...])
# Manual parsing required
```

### New Way (Recommended)
```python
# New approach - industry standard
completion = await client.parse(
    messages=[...],
    response_format=UserProfile
)
user = completion.parsed  # Already parsed and validated!
```

## Advanced Usage

### Complex Nested Models

```python
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
# OR from satya import Model, Field

class Address(BaseModel):  # or Model
    street: str
    city: str
    country: str

class UserProfile(BaseModel):  # or Model
    name: str
    addresses: List[Address]
    created_at: datetime
    premium: Optional[bool] = None

# Works seamlessly with complex nested structures
completion = await client.parse(
    messages=[{"role": "user", "content": "Create a user with multiple addresses"}],
    response_format=UserProfile
)
```

### Satya Batch Processing

For high-throughput applications, leverage Satya's batch processing:

```python
from satya import Model, Field

class UserProfile(Model):
    name: str = Field(description="User name")
    age: int = Field(description="User age")

# Configure batching for optimal performance
validator = UserProfile.validator()
validator.set_batch_size(1000)  # Recommended for most workloads

# Process large datasets efficiently
for valid_item in validator.validate_stream(large_dataset):
    process(valid_item)
```

### Streaming Not Supported

Note: The `parse()` method doesn't support streaming since structured parsing requires the complete response.

```python
# This will raise ValueError
await client.parse(messages=[...], response_format=UserProfile, stream=True)

# Use regular completion for streaming
async for chunk in await client.completion(messages=[...], stream=True):
    print(chunk)
```

## Examples

See the `examples/` directory for comprehensive examples:

- `examples/structured_outputs_new.py` - Complete demonstration with Pydantic
- `examples/structured_outputs_satya.py` - High-performance examples with Satya
- `examples/structured_outputs_comparison.py` - Old vs new approach comparison
- `examples/structured_outputs.py` - Legacy example (still works)

## Testing

Run the test suite to validate functionality:

```bash
# Test all structured outputs functionality
python -m pytest tests/test_structured_outputs*.py -v

# Test Pydantic integration
python -m pytest tests/test_structured_outputs.py -v

# Test Satya integration  
python -m pytest tests/test_structured_outputs_satya.py -v
```

## Compatibility

The new structured outputs implementation is compatible with:

- **OpenAI Chat Completions API** patterns
- **Anthropic Messages API** patterns  
- **All bhumi providers** (OpenAI, Anthropic, Gemini, Groq, etc.)
- **Existing bhumi code** (old methods still work but are deprecated)
- **Pydantic BaseModel** (standard validation)
- **Satya Model** (high-performance validation)

## Benefits

✅ **Industry Standard**: Follows OpenAI/Anthropic patterns  
✅ **High Performance**: Satya integration for production workloads  
✅ **Type Safety**: Full validation with structured response objects  
✅ **Developer Experience**: Clean, intuitive API  
✅ **Backward Compatible**: Existing code continues to work  
✅ **Comprehensive Testing**: Full test coverage  
✅ **Documentation**: Complete examples and guides

## Choosing Between Pydantic and Satya

**Use Pydantic when:**
- You need rich type coercion and defaults
- Complex nested validation logic
- Integration with existing Pydantic ecosystem
- Development/prototyping phase

**Use Satya when:**
- High-throughput production workloads
- Processing large datasets
- Memory-constrained environments
- Maximum performance is critical
- Batch/stream processing needed
