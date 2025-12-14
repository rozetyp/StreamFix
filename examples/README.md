# Examples Directory

This directory contains example integrations and usage patterns for StreamFix.

## Available Examples

### Basic Usage
- `python_openai.py` - Basic OpenAI SDK integration
- `javascript_openai.js` - Node.js OpenAI integration  
- `curl_examples.sh` - Command-line usage examples

### Framework Integrations
- `langchain_integration.py` - LangChain with StreamFix
- `llamaindex_integration.py` - LlamaIndex with StreamFix
- `autogen_integration.py` - AutoGen multi-agent integration

### Schema Validation Examples
- `contract_mode_basic.py` - Basic schema validation
- `complex_schemas.py` - Advanced schema patterns
- `error_handling.py` - Schema validation error handling

### Deployment Examples
- `docker_compose.yml` - Local Docker deployment
- `kubernetes.yaml` - Kubernetes deployment
- `railway_deploy.py` - Railway deployment script

## Running Examples

1. **Install StreamFix**:
   ```bash
   pip install streamfix
   ```

2. **Start local server**:
   ```bash
   streamfix serve
   ```

3. **Run an example**:
   ```bash
   python examples/python_openai.py
   ```

## Contributing Examples

Want to add an example? Please:
1. Create a new file with descriptive name
2. Add clear comments explaining the integration
3. Include both basic and advanced usage
4. Update this README with a brief description

Examples help the community learn StreamFix quickly!