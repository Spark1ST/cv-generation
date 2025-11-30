# API Integration Documentation for AI CV Generator

## Overview

The application relies on external APIs for generating CVs and evaluating career matches. The primary API integrations are:

1. **Google API**: Used for processing natural language and understanding user input.
2. **AgentOps API**: Manages the workflow of the agents responsible for CV generation, formatting, review, and evaluation.

## API Keys Configuration

To integrate the APIs into the system, you must provide API keys. Add the following keys to the `config/key.env` file:

- **GOOGLE_API_KEY**: API key for Google’s natural language processing.
- **AGENTOPS_API_KEY**: API key for the AgentOps service.

## API Calls

### 1. **Google API**

The Google API is used to process user input for tasks such as text summarization, language analysis, and more. The API is accessed through the `LLM` class in the codebase.

### 2. **AgentOps API**

AgentOps manages agent workflows for CV generation and evaluation. The system sends requests to AgentOps using the `agentops` library, which executes tasks based on defined agents.

For detailed API documentation, refer to the respective API providers' documentation.

---

### 4. **`RUBRIC.md`: Detailed Explanation of the Career Matching Evaluation Rubric and Its Scoring Criteria**
This document should explain how the career matching evaluation rubric works, including how each criterion is scored.
