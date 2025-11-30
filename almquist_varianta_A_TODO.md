# Almquist Multimodal GUI - VARIANTA A "STARTER"
## 📋 Detailní TODO List

---

## FÁZE 0: Příprava Prostředí (2-3 dny)

### ✅ Setup Development Environment
- [ ] Nainstalovat Node.js 20 LTS + npm
  ```bash
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
  nvm install 20
  nvm use 20
  ```

- [ ] Nainstalovat Python 3.11+ (už máš, zkontrolovat)
  ```bash
  python3 --version  # mělo by být >= 3.11
  ```

- [ ] Vytvořit projekt strukturu
  ```bash
  mkdir -p ~/almquist-multimodal/{frontend,backend,models,data}
  cd ~/almquist-multimodal
  git init
  ```

- [ ] Setup Git repository
  ```bash
  git remote add origin <your-repo-url>
  echo "node_modules/" >> .gitignore
  echo "*.pyc" >> .gitignore
  echo "models/*.bin" >> .gitignore
  echo ".env" >> .gitignore
  ```

### ✅ Backend Prerequisites
- [ ] Vytvořit Python virtual environment
  ```bash
  cd ~/almquist-multimodal/backend
  python3 -m venv venv
  source venv/bin/activate
  ```

- [ ] Nainstalovat základní dependencies
  ```bash
  pip install fastapi uvicorn[standard] websockets
  pip install langchain langchain-community
  pip install chromadb sentence-transformers
  pip install pydantic python-dotenv
  ```

- [ ] Nainstalovat Piper TTS
  ```bash
  pip install piper-tts
  # Stáhnout model
  mkdir -p models/piper
  cd models/piper
  wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
  wget https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
  ```

- [ ] Ověřit Ollama běží
  ```bash
  ollama list
  ollama pull llama3.2:latest
  ```

### ✅ Frontend Prerequisites
- [ ] Inicializovat Electron + React projekt
  ```bash
  cd ~/almquist-multimodal/frontend
  npx create-react-app . --template typescript
  npm install electron electron-builder --save-dev
  npm install @electron/remote
  ```

- [ ] Nainstalovat UI knihovny
  ```bash
  npm install tailwindcss @headlessui/react
  npm install react-player  # pro video
  npm install @types/node --save-dev
  ```

---

## FÁZE 1: Backend Core (1 týden)

### 🔧 FastAPI Server Setup
- [ ] Vytvořit `backend/main.py` s FastAPI app
  ```python
  from fastapi import FastAPI, WebSocket
  from fastapi.middleware.cors import CORSMiddleware

  app = FastAPI(title="Almquist Backend")

  # CORS pro Electron
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],
      allow_methods=["*"],
      allow_headers=["*"],
  )

  @app.get("/health")
  async def health():
      return {"status": "healthy"}
  ```

- [ ] Implementovat WebSocket endpoint pro chat
  ```python
  @app.websocket("/ws/chat")
  async def websocket_chat(websocket: WebSocket):
      await websocket.accept()
      # Logic zde
  ```

- [ ] Vytvořit `backend/config.py` pro settings
  ```python
  from pydantic_settings import BaseSettings

  class Settings(BaseSettings):
      OLLAMA_URL: str = "http://localhost:11434"
      CHROMA_PERSIST_DIR: str = "./data/chroma"
      PIPER_MODEL_PATH: str = "./models/piper"

      class Config:
          env_file = ".env"
  ```

- [ ] Test backend spuštění
  ```bash
  uvicorn main:app --reload --host 0.0.0.0 --port 8000
  # Mělo by běžet na http://localhost:8000/docs
  ```

### 🤖 LLM Integration (Ollama)
- [ ] Vytvořit `backend/services/llm_service.py`
  ```python
  from langchain_community.llms import Ollama
  from langchain.prompts import ChatPromptTemplate

  class LLMService:
      def __init__(self):
          self.llm = Ollama(model="llama3.2")

      async def generate_response(self, user_message: str, context: str = ""):
          # Logic zde
          pass
  ```

- [ ] Implementovat conversation history management
- [ ] Přidat system prompt pro Almquist personality
- [ ] Test LLM odpovědí
  ```bash
  curl http://localhost:8000/api/chat -d '{"message": "Hello"}'
  ```

### 🗃️ RAG System Setup
- [ ] Vytvořit `backend/services/rag_service.py`
  ```python
  from langchain_community.vectorstores import Chroma
  from langchain_community.embeddings import HuggingFaceEmbeddings

  class RAGService:
      def __init__(self):
          self.embeddings = HuggingFaceEmbeddings(
              model_name="sentence-transformers/all-MiniLM-L6-v2"
          )
          self.vectorstore = Chroma(
              persist_directory="./data/chroma",
              embedding_function=self.embeddings
          )

      async def search(self, query: str, k: int = 3):
          results = self.vectorstore.similarity_search(query, k=k)
          return results
  ```

- [ ] Připravit seed data pro RAG
  - [ ] Stáhnout Alexa Prize témata (movies, sports, news)
  - [ ] Stáhnout Wikipedia articles (top 1000 populárních článků)
  - [ ] Vytvořit `backend/scripts/prepare_rag_data.py`

- [ ] Naplnit Chroma DB daty
  ```bash
  python scripts/prepare_rag_data.py
  ```

- [ ] Test RAG vyhledávání
  ```python
  # Test script
  rag = RAGService()
  results = rag.search("Who won the 2023 NBA championship?")
  print(results)
  ```

### 🔊 TTS Integration (Piper)
- [ ] Vytvořit `backend/services/tts_service.py`
  ```python
  from piper import PiperVoice
  import wave

  class TTSService:
      def __init__(self, model_path: str):
          self.voice = PiperVoice.load(model_path)

      async def synthesize(self, text: str) -> bytes:
          # Generate audio
          audio = self.voice.synthesize(text)
          return audio
  ```

- [ ] Implementovat streaming audio response
- [ ] Test TTS generování
  ```bash
  curl http://localhost:8000/api/tts -d '{"text": "Hello world"}' -o test.wav
  aplay test.wav
  ```

---

## FÁZE 2: Frontend GUI (2 týdny)

### 🖼️ Electron Window Setup
- [ ] Upravit `frontend/public/electron.js`
  ```javascript
  const { app, BrowserWindow } = require('electron');

  function createWindow() {
      const win = new BrowserWindow({
          width: 1400,
          height: 900,
          webPreferences: {
              nodeIntegration: true,
              contextIsolation: false
          }
      });

      win.loadURL('http://localhost:3000');
  }

  app.whenReady().then(createWindow);
  ```

- [ ] Přidat scripts do `package.json`
  ```json
  "scripts": {
      "start": "react-scripts start",
      "electron": "electron .",
      "electron-dev": "ELECTRON_START_URL=http://localhost:3000 electron .",
      "build": "react-scripts build && electron-builder"
  }
  ```

- [ ] Test Electron spuštění
  ```bash
  npm run start  # v jednom terminálu
  npm run electron-dev  # v druhém terminálu
  ```

### 🎨 Main UI Components
- [ ] Vytvořit `src/components/ChatInterface.tsx`
  - [ ] Message list (scroll container)
  - [ ] Message bubbles (user vs bot)
  - [ ] Typing indicator
  - [ ] Input field + send button
  - [ ] Voice input button (pro budoucnost)

- [ ] Vytvořit `src/components/Avatar.tsx`
  - [ ] Static avatar obrázek
  - [ ] Basic CSS animace (breathing, talking)
  - [ ] Emotion states (happy, thinking, sad)

- [ ] Vytvořit `src/components/SidePanel.tsx`
  - [ ] Context information display
  - [ ] Wikipedia preview
  - [ ] Related topics
  - [ ] Quick actions

- [ ] Vytvořit `src/components/MediaViewer.tsx`
  - [ ] YouTube embed (react-player)
  - [ ] Image gallery
  - [ ] Fullscreen mode

### 🔗 WebSocket Client
- [ ] Vytvořit `src/services/websocketService.ts`
  ```typescript
  class WebSocketService {
      private ws: WebSocket | null = null;

      connect(url: string) {
          this.ws = new WebSocket(url);
          this.ws.onmessage = this.handleMessage;
          this.ws.onerror = this.handleError;
      }

      sendMessage(message: string) {
          if (this.ws && this.ws.readyState === WebSocket.OPEN) {
              this.ws.send(JSON.stringify({ message }));
          }
      }

      private handleMessage(event: MessageEvent) {
          const data = JSON.parse(event.data);
          // Handle bot response
      }
  }
  ```

- [ ] Připojit WebSocket k ChatInterface
- [ ] Implementovat reconnection logic
- [ ] Test real-time komunikace

### 🎨 Styling & Polish
- [ ] Setup TailwindCSS
  ```bash
  npx tailwindcss init
  ```

- [ ] Vytvořit theme colors
  ```javascript
  // tailwind.config.js
  theme: {
      extend: {
          colors: {
              'almquist-primary': '#3b82f6',
              'almquist-secondary': '#8b5cf6',
              'bot-bubble': '#f3f4f6',
              'user-bubble': '#3b82f6'
          }
      }
  }
  ```

- [ ] Design responsive layout (laptop, tablet)
- [ ] Add animations (framer-motion)
  ```bash
  npm install framer-motion
  ```

- [ ] Implement dark mode toggle

---

## FÁZE 3: Multimedia Integration (1 týden)

### 📺 Video Integration
- [ ] Vytvořit `backend/services/video_service.py`
  ```python
  import requests

  class VideoService:
      def __init__(self, youtube_api_key: str):
          self.api_key = youtube_api_key
          self.base_url = "https://www.googleapis.com/youtube/v3"

      async def search_videos(self, query: str, max_results: int = 3):
          # YouTube Data API search
          pass
  ```

- [ ] Získat YouTube Data API key
  - [ ] Jít na https://console.cloud.google.com
  - [ ] Vytvořit nový projekt
  - [ ] Enable YouTube Data API v3
  - [ ] Vytvořit credentials (API key)

- [ ] Implementovat video suggestions v GUI
- [ ] Test video playback v MediaViewer

### 🖼️ Image Integration
- [ ] Vytvořit `backend/services/image_service.py`
  ```python
  import requests
  from urllib.parse import quote

  class ImageService:
      async def get_wikipedia_images(self, article: str):
          # Wikipedia API pro obrázky
          pass

      async def search_unsplash(self, query: str):
          # Unsplash API (optional)
          pass
  ```

- [ ] Implementovat image grid v SidePanel
- [ ] Add image modal pro full view
- [ ] Test image loading & caching

### 🔍 Web Search Integration
- [ ] Implementovat Wikipedia API client
  ```python
  import wikipediaapi

  class WikiService:
      def __init__(self):
          self.wiki = wikipediaapi.Wikipedia('en')

      async def get_summary(self, title: str):
          page = self.wiki.page(title)
          return {
              "title": page.title,
              "summary": page.summary[:500],
              "url": page.fullurl
          }
  ```

- [ ] Přidat Wikipedia preview do SidePanel
- [ ] Implementovat "Learn more" action
- [ ] Test s různými dotazy

---

## FÁZE 4: Dialog Management (1 týden)

### 🧠 Dialog Manager
- [ ] Vytvořit `backend/services/dialog_manager.py`
  ```python
  from enum import Enum
  from typing import Dict, List

  class DialogState(Enum):
      GREETING = "greeting"
      CHITCHAT = "chitchat"
      TOPIC_DISCUSSION = "topic_discussion"
      ASKING_QUESTION = "asking_question"
      SHOWING_MEDIA = "showing_media"

  class DialogManager:
      def __init__(self):
          self.state = DialogState.GREETING
          self.context: Dict = {}
          self.history: List = []

      async def process_turn(self, user_input: str):
          # State machine logic
          pass
  ```

- [ ] Implementovat topic detection
  ```python
  topics = ["movies", "sports", "music", "news", "technology"]
  # Use zero-shot classification
  ```

- [ ] Přidat intent recognition
- [ ] Implementovat context tracking

### 🎯 Action System
- [ ] Vytvořit `backend/actions/` directory
  ```
  actions/
  ├── __init__.py
  ├── show_video.py
  ├── show_image.py
  ├── search_web.py
  └── tell_joke.py
  ```

- [ ] Implementovat každou action
  ```python
  # actions/show_video.py
  async def execute(query: str, context: dict):
      videos = await video_service.search_videos(query)
      return {
          "type": "video",
          "data": videos
      }
  ```

- [ ] Připojit actions k dialog manageru
- [ ] Test action triggering z chat

### 📊 Response Planning
- [ ] Implementovat "response planner"
  - [ ] Rozhodnout kdy zobrazit media
  - [ ] Kdy dát text odpověď
  - [ ] Kdy použít RAG
  - [ ] Kdy použít čistý LLM

- [ ] Vytvořit prompt templates
  ```python
  PROMPTS = {
      "chitchat": "You are Almquist, a friendly AI...",
      "explain_topic": "Explain {topic} in a simple way...",
      "tell_story": "Tell an interesting story about {subject}..."
  }
  ```

- [ ] Test různých conversation flows

---

## FÁZE 5: Testing & Polish (1 týden)

### 🧪 Testing
- [ ] Unit tests pro backend services
  ```bash
  pip install pytest pytest-asyncio
  ```

- [ ] Vytvořit `backend/tests/test_llm_service.py`
- [ ] Vytvořit `backend/tests/test_rag_service.py`
- [ ] Vytvořit `backend/tests/test_dialog_manager.py`

- [ ] Integration tests
  ```bash
  pytest tests/ -v
  ```

- [ ] Frontend tests (Jest)
  ```bash
  npm test
  ```

- [ ] E2E tests (Playwright - optional)
  ```bash
  npm install @playwright/test
  npx playwright test
  ```

### 🐛 Bug Fixes & Optimization
- [ ] Profiling backend performance
  ```bash
  python -m cProfile main.py
  ```

- [ ] Optimize RAG queries (caching)
- [ ] Optimize LLM inference (batching)
- [ ] Fix memory leaks
- [ ] Improve error handling

### 📝 Documentation
- [ ] Napsat README.md
  - [ ] Installation instructions
  - [ ] Configuration
  - [ ] Running the app
  - [ ] Troubleshooting

- [ ] API documentation (FastAPI Swagger)
- [ ] Code comments
- [ ] Architecture diagram
  ```bash
  # Použít draw.io nebo Mermaid
  ```

### 🎨 UI/UX Improvements
- [ ] User testing (3-5 lidí)
- [ ] Collect feedback
- [ ] Improve based on feedback:
  - [ ] Response times
  - [ ] Visual clarity
  - [ ] Conversation flow
  - [ ] Error messages

---

## FÁZE 6: Deployment & Packaging (3-4 dny)

### 📦 Packaging
- [ ] Build frontend production
  ```bash
  cd frontend
  npm run build
  ```

- [ ] Configure Electron Builder
  ```json
  // package.json
  "build": {
      "appId": "com.almquist.multimodal",
      "productName": "Almquist",
      "files": [
          "build/**/*",
          "node_modules/**/*",
          "public/electron.js"
      ],
      "directories": {
          "buildResources": "assets"
      },
      "linux": {
          "target": ["AppImage", "deb"]
      }
  }
  ```

- [ ] Build executable
  ```bash
  npm run electron:build
  ```

- [ ] Test instalace na čistém systému

### 🐳 Docker Setup (Optional)
- [ ] Vytvořit `backend/Dockerfile`
  ```dockerfile
  FROM python:3.11-slim

  WORKDIR /app
  COPY requirements.txt .
  RUN pip install -r requirements.txt

  COPY . .

  CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```

- [ ] Vytvořit `docker-compose.yml`
  ```yaml
  version: '3.8'
  services:
      backend:
          build: ./backend
          ports:
              - "8000:8000"
          volumes:
              - ./data:/app/data
              - ./models:/app/models
  ```

- [ ] Test Docker build
  ```bash
  docker-compose up --build
  ```

### 📊 Monitoring Setup
- [ ] Add logging (Python logging module)
- [ ] Setup basic metrics
  - [ ] Request count
  - [ ] Response times
  - [ ] Error rates

- [ ] Optional: Integrate s tvým Grafana stackem
  ```python
  from prometheus_client import Counter, Histogram

  requests_total = Counter('almquist_requests_total', 'Total requests')
  response_time = Histogram('almquist_response_time', 'Response time')
  ```

---

## FÁZE 7: Launch & Iterate (ongoing)

### 🚀 Launch
- [ ] Create launch checklist
- [ ] Final testing round
- [ ] Backup data
- [ ] Deploy to production

### 📈 Post-Launch
- [ ] Monitor logs daily (first week)
- [ ] Track user sessions
- [ ] Collect user feedback
- [ ] Fix critical bugs

### 🔄 Iteration
- [ ] Weekly updates plan
- [ ] Feature requests tracking
- [ ] Performance improvements
- [ ] Prepare for Varianta B features

---

## 🎯 Success Criteria

Po dokončení všech fází bys měl mít:

✅ Funkční Electron aplikace s chat GUI
✅ Backend s FastAPI + WebSocket
✅ LLM integration (Ollama)
✅ RAG system (Chroma + embeddings)
✅ TTS (Piper)
✅ Multimedia integration (video, images)
✅ Wikipedia search
✅ Basic dialog management
✅ Tests (unit + integration)
✅ Documentation
✅ Packaged executable

**Estimated total time:** 6-8 týdnů (120-160 hodin)

---

## 🆘 Troubleshooting

### Časté problémy:

**Ollama nefunguje:**
```bash
systemctl status ollama
ollama serve
```

**Chroma DB chyby:**
```bash
rm -rf data/chroma  # reset DB
python scripts/prepare_rag_data.py  # znovu naplnit
```

**Electron neotevře okno:**
- Check ELECTRON_START_URL
- Check React dev server běží (port 3000)
- Check console errors (Ctrl+Shift+I)

**WebSocket connection failed:**
- Check FastAPI server běží (port 8000)
- Check CORS settings
- Check firewall

---

## 📚 Resources

### Dokumentace:
- FastAPI: https://fastapi.tiangolo.com/
- Electron: https://www.electronjs.org/docs
- React: https://react.dev/
- LangChain: https://python.langchain.com/
- Piper TTS: https://github.com/rhasspy/piper

### Tutoriály:
- Electron + React: https://www.electronforge.io/guides/framework-integration/react
- WebSocket in FastAPI: https://fastapi.tiangolo.com/advanced/websockets/
- RAG with LangChain: https://python.langchain.com/docs/use_cases/question_answering/

---

*Varianta A TODO vytvořen: 2025-11-24*
*Estimated completion: 6-8 týdnů*
