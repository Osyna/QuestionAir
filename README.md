# QCM Generator and Quiz System

System for generating, managing, and delivering multiple-choice questions (QCM - Questionnaire à Choix Multiples) from educational content. The system uses LLaMA for question generation, embeddings for keyword extraction, and provides both API and web interfaces for quiz delivery.


## 🌟 Features

- **Intelligent Question Generation**
  - Automatic generation of multiple-choice questions from markdown content
  - Keyword extraction using embedding-based similarity
  - Natural language processing for French content
  - Quality control and validation of generated questions

- **Flexible Backend API**
  - RESTful endpoints for question retrieval and quiz generation
  - Subject and keyword-based filtering
  - Random question selection
  - Comprehensive statistics

- **Modern Web Interface**
  - Clean, responsive design using Next.js and Tailwind CSS
  - Subject-based quiz selection
  - Interactive quiz taking experience
  - Immediate feedback and scoring

## 🛠️ Technology Stack

- **Question Generation**
  - Python 3.8+
  - LLaMA 3.1 (via Ollama)
  - spaCy (French language model)
  - nomic-embed-text for embeddings

- **Backend**
  - FastAPI
  - SQLite
  - Pydantic
  - uvicorn

- **Frontend**
  - Next.js 14
  - React
  - TypeScript
  - Tailwind CSS

## 📋 Prerequisites

1. **Ollama Setup**
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.com/install.sh | sh
   
   # Pull required models
   ollama pull llama3.1:latest
   ollama pull nomic-embed-text
   ```

2. **Python Dependencies**
   ```bash
   pip install -r requirements.txt
   python -m spacy download fr_core_news_md
   ```

3. **Node.js Dependencies**
   ```bash
   cd frontend
   npm install
   ```

## 🚀 Installation & Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/qcm-system.git
   cd qcm-system
   ```

2. **Set Up the Database**
   ```bash
   # Generate questions from markdown files
   python question_generator/main.py
   ```

3. **Start the Backend Server**
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

4. **Launch the Frontend**
   ```bash
   cd frontend
   npm run dev
   ```

## 🔧 Configuration

### Question Generator Settings

```python
# config.py
GENERATOR_CONFIG = {
    "model": "llama3.1:latest",
    "embedding_model": "nomic-embed-text",
    "num_questions_per_file": 5,
    "min_content_length": 200
}
```

### API Configuration

```python
# main.py
app = FastAPI(
    title="QCM API",
    description="API for serving multiple-choice questions",
    version="1.0.0"
)
```

### Frontend Environment Variables

```env
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🎯 Usage

### Generating Questions

1. Prepare your educational content in markdown files:
   ```markdown
   # Topic Title
   
   Educational content goes here...
   ```

2. Run the question generator:
   ```bash
   python question_generator/main.py --input-dir /path/to/markdown/files
   ```

### Using the API

1. Get Available Subjects:
   ```bash
   curl http://localhost:8000/subjects
   ```

2. Generate a Quiz:
   ```bash
   curl "http://localhost:8000/quiz/generate?num_questions=10&subject=Mathematics"
   ```

### Taking a Quiz

1. Visit `http://localhost:3000` in your browser
2. Select a subject
3. Start the quiz
4. Answer questions and get immediate feedback

## 📚 API Documentation

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/subjects` | List all available subjects |
| GET | `/keywords` | List all keywords |
| GET | `/questions/random` | Get a random question |
| GET | `/quiz/generate` | Generate a quiz |
| GET | `/stats` | Get database statistics |

### Example Response

```json
{
  "id": 1,
  "subject": "Mathematics",
  "question_text": "What is 2+2?",
  "choices": {
    "A": "3",
    "B": "4",
    "C": "5",
    "D": "6"
  },
  "answers": ["B"]
}
```

## 🧪 Testing

```bash
# Backend tests
pytest backend/tests/

# Frontend tests
cd frontend
npm test
```

## 👏 Acknowledgments

- LLaMA team for the language model
- Ollama team for the model serving infrastructure
- spaCy team for the French language model
- All contributors who have helped shape this project



## 🔮 Future Improvements

- [ ] More question types beyond multiple choice
- [ ] Enhanced analytics and reporting
- [ ] User authentication and progress tracking
