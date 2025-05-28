# Contributing to AI Document Processor

First off, thank you for considering contributing to AI Document Processor! It's people like you that make this tool better for everyone. 🎉

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## How Can I Contribute?

### 🐛 Reporting Bugs

Before creating bug reports, please check existing issues as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples**
- **Include screenshots if possible**
- **Describe the behavior you observed and what you expected**
- **Include your environment details** (OS, Python version, Node version, etc.)

### 💡 Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

- **Use a clear and descriptive title**
- **Provide a detailed description of the suggested enhancement**
- **Provide specific examples to demonstrate the feature**
- **Describe the current behavior and expected behavior**
- **Explain why this enhancement would be useful**

### 🔧 Pull Requests

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. If you've changed APIs, update the documentation
4. Ensure the test suite passes
5. Make sure your code follows the style guidelines
6. Issue that pull request!

## Development Setup

```bash
# 1. Fork and clone the repository
git clone https://github.com/your-username/ai-document-processor.git
cd ai-document-processor

# 2. Create a virtual environment for Python
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 3. Install frontend dependencies
cd ../frontend
npm install

# 4. Copy environment files
cp .env.example .env
# Add your OPENAI_API_KEY to .env

# 5. Run the development environment
cd ..
./scripts/dev.sh
```

## Style Guidelines

### Python (Backend)

We use [Black](https://github.com/psf/black) for Python code formatting:

```bash
cd backend
black app/
flake8 app/
```

### TypeScript/JavaScript (Frontend)

We use ESLint and Prettier:

```bash
cd frontend
npm run lint
npm run format
```

### Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

Examples:
```
feat: Add batch processing for multiple PDFs
fix: Resolve memory leak in image processing
docs: Update API documentation for new endpoints
style: Format code with Black
test: Add tests for Excel export functionality
```

## Testing

### Backend Tests

```bash
cd backend
pytest
pytest --cov=app  # With coverage
```

### Frontend Tests

```bash
cd frontend
npm test
npm run test:coverage
```

## Project Structure

```
document-processor/
├── backend/          # FastAPI backend
│   ├── app/
│   │   ├── api/     # API endpoints
│   │   ├── core/    # Core configuration
│   │   ├── models/  # Database models
│   │   ├── schemas/ # Pydantic schemas
│   │   └── services/# Business logic
│   └── tests/       # Backend tests
├── frontend/        # Next.js frontend
│   ├── src/
│   │   ├── app/     # App router pages
│   │   ├── components/
│   │   └── lib/     # Utilities
│   └── tests/       # Frontend tests
└── scripts/         # Utility scripts
```

## Additional Notes

### Performance Considerations

- Keep PDF processing under 30 seconds per page
- Minimize API calls to OpenAI
- Use caching where appropriate
- Optimize image preprocessing

### Security

- Never commit API keys or secrets
- Validate all user inputs
- Use parameterized queries
- Follow OWASP guidelines

## Questions?

Feel free to open an issue for any questions. We're here to help!

Thank you for contributing! 🚀