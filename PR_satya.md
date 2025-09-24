# PR: Enhanced Nested Model Validation Support in Satya

## Summary

This PR proposes enhancements to Satya's model validation system to better support complex nested structures, particularly `Dict[str, CustomModel]` patterns commonly used in machine learning applications like MAP-Elites archives, configuration management, and hierarchical data structures.

## Problem Statement

### Current Limitation
Satya v0.3.6 provides excellent validation for individual models and simple nested structures, but struggles with complex nested model validation involving dictionaries of custom types. For example:

```python
from satya import Model, Field

class SystemConfig(Model):
    buffer_size: int = Field(ge=256, le=100000)
    # ... other fields

class ArchiveEntry(Model):
    config: SystemConfig = Field(description="System configuration")
    performance: float = Field(ge=-1000.0, le=100000.0)

class MapElitesArchive(Model):
    resolution: int = Field(ge=1, le=20)
    archive: Dict[str, ArchiveEntry] = Field(description="Archive entries")
```

**Current Behavior**: Validation fails with `"Custom type ArchiveEntry not found"` when attempting to validate the `MapElitesArchive` model.

### Impact
This limitation affects several important use cases:
- **MAP-Elites algorithms** for evolutionary optimization
- **Configuration management systems** with hierarchical structures
- **Machine learning pipelines** with complex parameter spaces
- **Scientific data structures** with nested experimental results

## Proposed Solution

### Core Enhancement: Recursive Model Resolution

Implement recursive model type resolution that can handle nested custom types in dictionary values and other complex structures.

#### Key Changes

1. **Enhanced Type Registry**
   - Expand the internal model registry to track nested model dependencies
   - Implement topological sorting for model validation order
   - Add circular dependency detection

2. **Improved Dictionary Validation**
   - Support for `Dict[str, CustomModel]` patterns
   - Support for `Dict[int, CustomModel]` and other key types
   - Recursive validation of nested model instances

3. **Better Error Messages**
   - More descriptive error messages for nested model failures
   - Suggestions for alternative validation approaches
   - Clear guidance on model registration order

### Implementation Approach

#### Phase 1: Registry Enhancement
```python
class ModelRegistry:
    def __init__(self):
        self._models = {}
        self._dependencies = {}

    def register_model(self, model_class: Type[Model]):
        """Register a model and analyze its dependencies"""
        self._models[model_class.__name__] = model_class
        self._analyze_dependencies(model_class)

    def _analyze_dependencies(self, model_class: Type[Model]):
        """Analyze and record model dependencies"""
        # Implementation to extract nested model types
        # from annotations like Dict[str, ArchiveEntry]

    def validate_with_dependencies(self, model_class: Type[Model], data: dict):
        """Validate model and all its dependencies in correct order"""
        # Implementation using topological sort
```

#### Phase 2: Enhanced Validator
```python
class EnhancedValidator:
    def __init__(self):
        self.registry = ModelRegistry()

    def validate_nested_model(self, model_class: Type[Model], data: dict):
        """Validate model with full nested support"""
        # 1. Register model and dependencies
        # 2. Validate in dependency order
        # 3. Handle nested Dict[str, Model] patterns
        # 4. Provide detailed error reporting
```

#### Phase 3: Backward Compatibility
- Ensure all existing validation continues to work
- Add opt-in flag for enhanced nested validation
- Provide migration path for complex use cases

## Use Cases and Examples

### MAP-Elites Archive Validation

```python
# Current workaround (manual validation)
class MapElitesBuffer:
    def _load_archive_fast(self, archive_path: str):
        with open(archive_path, 'rb') as f:
            raw_data = orjson.loads(f.read())

        self.archive = {}
        for coord_str, entry_data in raw_data["archive"].items():
            coord_tuple = self._parse_coordinate_tuple(coord_str)
            config = SystemConfig(**entry_data["config"])  # Manual validation
            performance = float(entry_data["performance"])
            self.archive[coord_tuple] = (config, performance)

# Proposed with enhanced Satya
class MapElitesArchive(Model):
    resolution: int = Field(ge=1, le=20)
    archive: Dict[str, ArchiveEntry] = Field(description="Archive entries")

class MapElitesBuffer:
    def _load_archive_fast(self, archive_path: str):
        with open(archive_path, 'rb') as f:
            raw_data = orjson.loads(f.read())

        # Full validation with nested models
        archive_model = MapElitesArchive(**raw_data)

        # Convert to internal format
        self.archive = {}
        for coord_str, entry in archive_model.archive.items():
            coord_tuple = self._parse_coordinate_tuple(coord_str)
            self.archive[coord_tuple] = (entry.config, entry.performance)
```

### Configuration Management

```python
class ServiceConfig(Model):
    name: str
    port: int = Field(ge=1024, le=65535)
    dependencies: List[str] = Field(default_factory=list)

class EnvironmentConfig(Model):
    name: str
    services: Dict[str, ServiceConfig] = Field(description="Service configurations")

# Current: Manual validation required
# Proposed: Direct model validation
env_config = EnvironmentConfig(**config_data)
```

### Machine Learning Pipelines

```python
class ModelParams(Model):
    learning_rate: float = Field(ge=0.0, le=1.0)
    batch_size: int = Field(ge=1, le=10000)
    layers: List[int] = Field(min_items=1)

class ExperimentResult(Model):
    model_params: ModelParams
    accuracy: float = Field(ge=0.0, le=1.0)
    training_time: float = Field(ge=0.0)

class ExperimentSuite(Model):
    experiments: Dict[str, ExperimentResult] = Field(description="Experiment results")

# Enables full validation of complex ML experiment data
suite = ExperimentSuite(**experiment_data)
```

## Benefits

### Performance Improvements
- **Single-pass validation**: Validate entire nested structure in one operation
- **Early failure detection**: Catch validation errors at the root level
- **Reduced code complexity**: Eliminate manual validation loops

### Developer Experience
- **Type safety**: Full type checking for nested structures
- **IntelliSense support**: Better IDE support for complex data structures
- **Schema generation**: Enhanced OpenAI-compatible schema generation for nested models

### Reliability
- **Comprehensive validation**: No missed validation edge cases
- **Better error messages**: Clear indication of validation failures in nested structures
- **Consistency**: Uniform validation behavior across all nesting levels

## Implementation Details

### Type Analysis
```python
def extract_nested_models(cls: Type[Model]) -> Set[Type[Model]]:
    """Extract all nested model types from a model class"""
    nested_models = set()

    for field_name, field_info in cls.__annotations__.items():
        origin = get_origin(field_info)
        args = get_args(field_info)

        if origin == dict:
            # Handle Dict[str, CustomModel] patterns
            value_type = args[1]
            if is_model_class(value_type):
                nested_models.add(value_type)
                # Recursively extract nested models
                nested_models.update(extract_nested_models(value_type))
        elif origin in (list, tuple):
            # Handle List[CustomModel] patterns
            item_type = args[0]
            if is_model_class(item_type):
                nested_models.add(item_type)
                nested_models.update(extract_nested_models(item_type))
        elif is_model_class(field_info):
            # Handle direct model references
            nested_models.add(field_info)
            nested_models.update(extract_nested_models(field_info))

    return nested_models
```

### Validation Order Resolution
```python
def resolve_validation_order(models: Set[Type[Model]]) -> List[Type[Model]]:
    """Resolve validation order using topological sort"""
    # Implementation of topological sort for model dependencies
    # Ensures base models are validated before dependent models
    pass
```

## Testing Strategy

### Comprehensive Test Suite
- **Unit tests**: Individual component validation
- **Integration tests**: Full nested model validation
- **Performance tests**: Benchmark against manual validation approaches
- **Edge case tests**: Circular dependencies, deep nesting, large datasets

### Benchmarking
```python
def benchmark_nested_validation():
    """Compare performance of enhanced vs manual validation"""

    # Test with MAP-Elites archive data
    # Measure validation time, memory usage, error detection rate

    # Results should show:
    # - Faster validation with enhanced approach
    # - Better error reporting
    # - Reduced code complexity
```

## Migration Path

### Backward Compatibility
- All existing code continues to work unchanged
- Enhanced features are opt-in via configuration flags
- Clear migration guide with before/after examples

### Deprecation Strategy
- Add deprecation warnings for manual validation workarounds
- Provide automated migration tools
- Maintain support for legacy validation patterns

## Conclusion

This enhancement would significantly improve Satya's capabilities for complex, real-world data validation scenarios while maintaining backward compatibility and performance. The MAP-Elites use case demonstrates the immediate practical value, but the improvements would benefit a wide range of applications dealing with hierarchical and nested data structures.

## Implementation Timeline
- **Phase 1** (2 weeks): Core registry and type analysis
- **Phase 2** (2 weeks): Enhanced validator implementation
- **Phase 3** (1 week): Testing and documentation
- **Phase 4** (1 week): Performance optimization and final validation

---

**Labels**: enhancement, validation, nested-models, performance, developer-experience
**Priority**: High
**Complexity**: Medium-High
