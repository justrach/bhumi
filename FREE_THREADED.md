# 🚀 Bhumi Free-Threaded Python Support

## Overview

Bhumi now supports **free-threaded Python 3.13+** for true parallel execution without the Global Interpreter Lock (GIL)! This means Bhumi can run on **STEROIDS** 🔥 with maximum performance.

## What is Free-Threaded Python?

Python 3.13 introduced an experimental free-threaded build (3.13t) that removes the GIL, allowing:
- **True parallel execution** of Python code across multiple CPU cores
- **No GIL contention** for CPU-bound operations
- **Maximum performance** for concurrent workloads

## Bhumi's Free-Threaded Implementation

### Key Features

✅ **GIL-Free Module**: Declared with `#[pymodule(gil_used = false)]`  
✅ **Thread-Safe Classes**: All `#[pyclass]` types implement `Sync`  
✅ **Parallel Execution**: Multiple threads can execute Bhumi operations simultaneously  
✅ **Zero GIL Overhead**: No GIL acquisition/release in hot paths  
✅ **Backward Compatible**: Works with both GIL-enabled and GIL-disabled Python  

### Technical Implementation

#### 1. Module Declaration
```rust
#[pymodule(gil_used = false)]
fn bhumi(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<LLMResponse>()?;
    m.add_class::<BhumiCore>()?;
    Ok(())
}
```

#### 2. Thread-Safe Classes
```rust
// LLMResponse - immutable and frozen
#[pyclass(frozen)]
struct LLMResponse {
    text: String,
    raw_response: String,
}
unsafe impl Sync for LLMResponse {}

// BhumiCore - uses Arc<Mutex/RwLock> for thread safety
#[pyclass]
struct BhumiCore {
    sender: Arc<tokio::sync::Mutex<mpsc::Sender<String>>>,
    response_receiver: Arc<tokio::sync::Mutex<mpsc::Receiver<String>>>,
    runtime: Arc<tokio::runtime::Runtime>,
    // ... other fields
}
unsafe impl Sync for BhumiCore {}
```

#### 3. Synchronization Primitives
- **`Arc<tokio::sync::Mutex<T>>`**: Thread-safe async mutex
- **`Arc<tokio::sync::RwLock<T>>`**: Thread-safe async read-write lock
- **`Arc<std::sync::Mutex<T>>`**: Thread-safe sync mutex
- All primitives are `Send + Sync` for safe multi-threaded access

## Performance Benefits

### With GIL (Traditional Python)
- Single thread execution at a time
- GIL contention overhead
- Limited parallelism for CPU-bound tasks

### Without GIL (Free-Threaded Python 3.13+)
- **True parallel execution** across all CPU cores
- **Zero GIL overhead** in Bhumi operations
- **Maximum throughput** for concurrent LLM requests
- **Scalable performance** with thread count

## Usage

### Requirements
- Python 3.13+ with free-threaded build (3.13t)
- Install with: `python3.13t -m pip install bhumi`

### Example: Parallel LLM Requests
```python
from concurrent.futures import ThreadPoolExecutor
from bhumi import bhumi

# Create multiple Bhumi instances
cores = [
    bhumi.BhumiCore(
        max_concurrent=10,
        provider="openai",
        model="gpt-4"
    )
    for _ in range(4)
]

# Execute in true parallel (no GIL!)
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [
        executor.submit(core.completion, model, messages, api_key)
        for core in cores
    ]
    results = [f.result() for f in futures]
```

### Checking GIL Status
```python
import sys

if hasattr(sys, '_is_gil_enabled'):
    if sys._is_gil_enabled():
        print("GIL is ENABLED")
    else:
        print("GIL is DISABLED - Bhumi on STEROIDS! 🚀")
```

## Building from Source

### For Free-Threaded Python
```bash
# Build with maturin
maturin build --release

# Install the wheel
pip install target/wheels/bhumi-*.whl
```

### Dependencies
- PyO3 0.26+ with free-threaded support
- Tokio 1.47+ for async runtime
- No orjson dependency (uses stdlib json)

## Compatibility

| Python Version | GIL Status | Bhumi Support |
|---------------|------------|---------------|
| 3.8 - 3.12    | Enabled    | ✅ Full support |
| 3.13 (standard) | Enabled  | ✅ Full support |
| 3.13t (free-threaded) | Disabled | ✅ **STEROIDS MODE** 🚀 |

## Migration Guide

### From GIL-based Python
No code changes needed! Bhumi automatically adapts:
- With GIL: Uses traditional thread safety
- Without GIL: Runs in true parallel mode

### Performance Tuning
For maximum performance with free-threaded Python:
1. Use `ThreadPoolExecutor` with `max_workers=cpu_count()`
2. Create separate `BhumiCore` instances per thread
3. Avoid shared state between threads
4. Let Bhumi's internal `Arc<Mutex>` handle synchronization

## Testing

Run the free-threaded test:
```bash
python test_free_threaded.py
```

Expected output:
```
🎉 GIL is DISABLED - running in true parallel mode!
   Bhumi is on STEROIDS! 🚀
```

## Technical Details

### Thread Safety Guarantees
- **LLMResponse**: Immutable (`frozen`), safe to share across threads
- **BhumiCore**: All mutable state protected by `Arc<Mutex>` or `Arc<RwLock>`
- **Tokio Runtime**: Thread-safe async runtime shared via `Arc`
- **No Data Races**: Rust's type system prevents data races at compile time

### Memory Model
- **Arc**: Atomic reference counting for shared ownership
- **Mutex/RwLock**: Mutual exclusion for mutable access
- **Send + Sync**: All types are safe to send and share across threads

## Future Enhancements

- [ ] Critical sections API for fine-grained locking
- [ ] Lock-free data structures for hot paths
- [ ] NUMA-aware thread pooling
- [ ] Per-thread statistics and monitoring

## References

- [PEP 703: Making the Global Interpreter Lock Optional](https://peps.python.org/pep-0703/)
- [PyO3 Free-Threading Guide](https://pyo3.rs/latest/free-threading)
- [Python 3.13 Release Notes](https://docs.python.org/3.13/whatsnew/3.13.html)

---

**Bhumi is now ready for the future of Python! 🚀**
