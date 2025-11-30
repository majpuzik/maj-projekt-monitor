# Almquist Multimodal GUI - VARIANTA B "PROFESSIONAL"
## 📋 Detailní TODO List

**Doporučená varianta pro Alexa Prize účast**

---

## FÁZE 0: Příprava & Planning (1 týden)

### 📐 Projekt Setup
- [ ] Vytvořit detailní project plan (Gantt chart)
- [ ] Setup project management tool (Linear/GitHub Projects)
- [ ] Vytvořit Git repository structure
  ```
  almquist-pro/
  ├── frontend/          # Electron + React + Three.js
  ├── backend/           # FastAPI + orchestration
  ├── models/            # AI models
  ├── services/          # Microservices (TTS, STT, Image gen)
  ├── data/              # RAG data, logs
  ├── docker/            # Docker compose files
  └── docs/              # Documentation
  ```

- [ ] Setup development environment
  - [ ] Docker Desktop
  - [ ] Node.js 20 LTS
  - [ ] Python 3.11+
  - [ ] CUDA Toolkit (pro GPU)
  - [ ] VS Code + extensions

### 🔧 Hardware Verification
- [ ] Ověřit GPU specs
  ```bash
  nvidia-smi
  # Check VRAM (potřeba min 16 GB pro SDXL)
  ```

- [ ] Test GPU performance
  ```bash
  pip install torch torchvision
  python -c "import torch; print(torch.cuda.is_available())"
  ```

- [ ] Benchmark pro modely:
  - [ ] Llama 3.2 70B inference speed
  - [ ] SDXL image generation time
  - [ ] MusicGen audio generation time

- [ ] Plán upgrade pokud potřeba (RTX 4090?)

### 📚 Research Phase
- [ ] Prostudovat Alexa Prize SGC5 proceedings
  - [ ] Stáhnout všechny winnig team papers
  - [ ] Analyzovat multimodal approaches
  - [ ] Note best practices

- [ ] Prostudovat Alquist 5.0 paper podrobně
- [ ] Research Ready Player Me avatar system
- [ ] Research Unreal Engine MetaHuman (pro future)

---

## FÁZE 1: Backend Infrastructure (2 týdny)

### 🏗️ Core Architecture
- [ ] Design microservices architecture
  ```
  ┌──────────────────────────────────┐
  │   API Gateway (FastAPI)          │
  ├──────────────────────────────────┤
  │  ┌────────┐  ┌────────┐         │
  │  │Dialog  │  │ RAG    │         │
  │  │Manager │  │Service │         │
  │  └────────┘  └────────┘         │
  ├──────────────────────────────────┤
  │  ┌────┐ ┌────┐ ┌────┐ ┌────┐   │
  │  │LLM │ │TTS │ │IMG │ │VID │   │
  │  └────┘ └────┘ └────┘ └────┘   │
  └──────────────────────────────────┘
  ```

- [ ] Setup Redis pro caching & task queue
  ```bash
  docker run -d -p 6379:6379 redis:alpine
  ```

- [ ] Setup PostgreSQL pro metadata
  ```bash
  docker run -d -p 5432:5432 \
    -e POSTGRES_PASSWORD=almquist \
    postgres:15
  ```

- [ ] Vytvořit `docker-compose.yml`
  ```yaml
  version: '3.8'
  services:
      redis:
          image: redis:alpine
      postgres:
          image: postgres:15
      qdrant:
          image: qdrant/qdrant:latest  # už máš
      backend:
          build: ./backend
          depends_on: [redis, postgres, qdrant]
  ```

### 🤖 Advanced LLM Setup
- [ ] Nainstalovat vLLM pro efficient inference
  ```bash
  pip install vllm
  ```

- [ ] Setup Llama 3.2 70B s vLLM
  ```python
  from vllm import LLM, SamplingParams

  llm = LLM(
      model="meta-llama/Llama-3.2-70b",
      tensor_parallel_size=2,  # pokud 2 GPU
      gpu_memory_utilization=0.9
  )
  ```

- [ ] Benchmark inference speed
  - [ ] Target: < 500ms pro 100 tokens
  - [ ] Pokud pomalé, zvážit quantization (AWQ/GPTQ)

- [ ] Setup Qwen2.5-VL pro vision tasks
  ```bash
  # Multimodal model pro image understanding
  ollama pull qwen2.5-vl:32b
  ```

- [ ] Vytvořit LLM router
  ```python
  class LLMRouter:
      async def route(self, task_type: str):
          if task_type == "vision":
              return qwen_vl
          elif task_type == "long_context":
              return llama_70b
          else:
              return llama_7b  # faster for simple tasks
  ```

### 🗂️ Advanced RAG System
- [ ] Migrate z Chroma na Qdrant (už máš běžící!)
  ```python
  from qdrant_client import QdrantClient
  from qdrant_client.models import Distance, VectorParams

  client = QdrantClient(host="localhost", port=6333)

  client.create_collection(
      collection_name="almquist_knowledge",
      vectors_config=VectorParams(size=768, distance=Distance.COSINE)
  )
  ```

- [ ] Setup better embeddings
  ```bash
  # Option 1: nomic-embed-text (open-source, top tier)
  ollama pull nomic-embed-text

  # Option 2: OpenAI (pokud budget)
  # text-embedding-3-large
  ```

- [ ] Implementovat hybrid search (vector + keyword)
  ```python
  class HybridRAG:
      async def search(self, query: str):
          # Vector search
          vector_results = await self.qdrant.search(query)
          # BM25 keyword search
          keyword_results = await self.bm25_index.search(query)
          # Merge & rerank
          return self.rerank(vector_results, keyword_results)
  ```

- [ ] Setup reranker
  ```bash
  pip install sentence-transformers
  # Use cross-encoder for reranking
  ```

- [ ] Prepare comprehensive knowledge base:
  - [ ] **Alexa Prize Corpus:**
    - [ ] Movies: IMDB top 1000 + Wikipedia
    - [ ] Sports: Major leagues data
    - [ ] Music: Artists, albums, charts
    - [ ] News: Recent events (crawl RSS feeds)
    - [ ] Technology: Latest trends

  - [ ] **Wikipedia:**
    - [ ] Top 10,000 articles
    - [ ] Preprocessed & chunked
    - [ ] With metadata (categories, links)

  - [ ] **YouTube:**
    - [ ] Trending videos metadata
    - [ ] Transcripts (kde dostupné)

- [ ] Vytvořit ingestion pipeline
  ```bash
  python scripts/ingest_wikipedia.py
  python scripts/ingest_alexa_corpus.py
  python scripts/ingest_youtube_metadata.py
  ```

- [ ] Test RAG quality
  - [ ] Precision@5 > 0.8
  - [ ] Response time < 200ms

### 🎙️ Audio System
- [ ] **TTS: Coqui XTTS v2** (high quality + voice cloning)
  ```bash
  pip install TTS
  tts --list_models
  tts --model_name tts_models/multilingual/multi-dataset/xtts_v2 \
      --text "Hello from Almquist" --out_path test.wav
  ```

- [ ] Vytvořit TTS service
  ```python
  from TTS.api import TTS

  class CoquiTTSService:
      def __init__(self):
          self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")

      async def synthesize(self, text: str, emotion: str = "neutral"):
          # Generate with emotion
          audio = self.tts.tts(text=text, emotion=emotion)
          return audio
  ```

- [ ] Implementovat voice cloning (optional)
  ```python
  # Clone from reference audio
  self.tts.tts_to_file(
      text="Hello",
      speaker_wav="reference.wav",  # tvůj hlas
      file_path="output.wav"
  )
  ```

- [ ] **STT: Whisper** (pro budoucí voice input)
  ```bash
  pip install openai-whisper
  # nebo faster-whisper pro GPU optimizaci
  pip install faster-whisper
  ```

- [ ] Test TTS latency
  - [ ] Target: < 2s pro krátkou větu
  - [ ] Streaming pokud možné

---

## FÁZE 2: Multimedia Services (2 týdny)

### 🖼️ Image Generation (Stable Diffusion)
- [ ] Nainstalovat AUTOMATIC1111 WebUI
  ```bash
  git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git
  cd stable-diffusion-webui
  ./webui.sh --api --listen
  ```

- [ ] Stáhnout SDXL model
  ```bash
  cd models/Stable-diffusion/
  wget https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors
  ```

- [ ] Install ControlNet (pro guided generation)
  - [ ] Extensions tab → Install ControlNet
  - [ ] Download ControlNet models (canny, depth, openpose)

- [ ] Vytvořit Image Service
  ```python
  import requests

  class StableDiffusionService:
      def __init__(self, api_url="http://localhost:7860"):
          self.api_url = api_url

      async def generate(self, prompt: str, negative_prompt: str = ""):
          payload = {
              "prompt": prompt,
              "negative_prompt": negative_prompt,
              "steps": 30,
              "width": 1024,
              "height": 1024,
              "cfg_scale": 7.5
          }
          response = requests.post(f"{self.api_url}/sdapi/v1/txt2img", json=payload)
          return response.json()["images"][0]  # base64
  ```

- [ ] Vytvořit prompt templates pro different topics
  ```python
  PROMPTS = {
      "movie": "cinematic scene of {subject}, movie poster style, detailed",
      "sports": "dynamic sports photo of {subject}, action shot, professional",
      "music": "album cover art for {subject}, artistic, vibrant colors",
      "nature": "beautiful nature photo of {subject}, national geographic style"
  }
  ```

- [ ] Test image generation speed
  - [ ] Target: < 5s na RTX 4090
  - [ ] Pokud pomalé, reduce steps nebo use LCM LoRA

- [ ] Implement image caching
  ```python
  # Cache based on prompt hash
  cache_key = hashlib.md5(prompt.encode()).hexdigest()
  ```

### 🎵 Music Generation (AudioCraft)
- [ ] Nainstalovat AudioCraft
  ```bash
  pip install audiocraft
  ```

- [ ] Setup MusicGen
  ```python
  from audiocraft.models import MusicGen

  class MusicService:
      def __init__(self):
          self.model = MusicGen.get_pretrained('facebook/musicgen-large')

      async def generate(self, description: str, duration: int = 10):
          self.model.set_generation_params(duration=duration)
          wav = self.model.generate([description])
          return wav
  ```

- [ ] Test music generation
  ```python
  music = await music_service.generate(
      "upbeat electronic dance music",
      duration=30
  )
  # Play or save
  ```

- [ ] Implementovat music styles
  ```python
  STYLES = {
      "lullaby": "soft, gentle piano melody, calming, slow tempo",
      "anthem": "powerful orchestral music, heroic, brass section",
      "background": "ambient, atmospheric, subtle, non-intrusive"
  }
  ```

- [ ] Test generation time
  - [ ] Target: < 30s pro 30s hudby
  - [ ] GPU acceleration critical

### 🎬 Video Integration
- [ ] YouTube Data API setup (už z Varianty A)

- [ ] **Video Generation** (AnimateDiff - optional, expensive)
  ```bash
  # Pro budoucnost - zatím skip, příliš náročné
  # Zaměřit se na video search & display
  ```

- [ ] Implement video suggestions
  ```python
  class VideoService:
      async def suggest_videos(self, topic: str, context: str):
          # Use LLM to generate search query
          search_query = await self.llm.generate_search_query(topic, context)
          # Search YouTube
          videos = await self.youtube_api.search(search_query, max_results=3)
          return videos
  ```

- [ ] Video metadata extraction
  - [ ] Title, description
  - [ ] Thumbnail
  - [ ] Duration
  - [ ] View count (pro sorting)

---

## FÁZE 3: Frontend - Advanced GUI (3 týdny)

### 🎨 3D Avatar System
- [ ] **Option A: Ready Player Me**
  ```bash
  npm install @readyplayerme/rpm-react-sdk
  ```

  ```typescript
  import { AvatarCreator } from '@readyplayerme/rpm-react-sdk';

  <AvatarCreator
      subdomain="almquist"
      onAvatarExported={(url) => setAvatarUrl(url)}
  />
  ```

- [ ] **Option B: VRM Avatar** (open standard)
  ```bash
  npm install @pixiv/three-vrm
  ```

  ```typescript
  import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader';
  import { VRMLoaderPlugin } from '@pixiv/three-vrm';

  const loader = new GLTFLoader();
  loader.register((parser) => new VRMLoaderPlugin(parser));
  loader.load('avatar.vrm', (gltf) => {
      const vrm = gltf.userData.vrm;
      scene.add(vrm.scene);
  });
  ```

- [ ] Vytvořit `components/Avatar3D.tsx`
  ```typescript
  import * as THREE from 'three';
  import { Canvas } from '@react-three-fiber';

  const Avatar3D = ({ emotion, isSpeaking }) => {
      return (
          <Canvas>
              <ambientLight intensity={0.5} />
              <spotLight position={[10, 10, 10]} />
              {/* Avatar model zde */}
          </Canvas>
      );
  };
  ```

- [ ] Implementovat animace:
  - [ ] **Idle** (breathing, blinking)
  - [ ] **Talking** (lip sync with audio)
  - [ ] **Emotions** (happy, sad, surprised, thinking)
  - [ ] **Gestures** (pointing, nodding, waving)

- [ ] Lip sync system
  ```typescript
  // Use Rhubarb Lip Sync nebo OVRLipSync
  npm install rhubarb-lip-sync
  ```

- [ ] Test performance
  - [ ] Target: 60 FPS
  - [ ] Optimize model polygons pokud laguje

### 🖥️ Main Interface Layout
- [ ] Design multi-panel layout
  ```
  ┌───────────────────────────────────────┐
  │  Header (Title, Settings, Minimize)  │
  ├──────────┬────────────────────────────┤
  │          │                            │
  │  Avatar  │      Chat Messages         │
  │  (3D)    │      (scrollable)          │
  │          │                            │
  │  300px   │                            │
  ├──────────┼────────────────────────────┤
  │          │  Input Field   [Send]  [🎤]│
  ├──────────┴────────────────────────────┤
  │   Media Viewer (images/video)         │
  │   (collapsible)                        │
  ├───────────────────────────────────────┤
  │   Context Panel (Wikipedia, etc)      │
  │   (collapsible)                        │
  └───────────────────────────────────────┘
  ```

- [ ] Vytvořit responsive layout (support různých sizes)

- [ ] Implementovat collapsible panels
  ```typescript
  const [mediaVisible, setMediaVisible] = useState(false);
  const [contextVisible, setContextVisible] = useState(true);
  ```

### 📊 Data Visualizations
- [ ] Nainstalovat visualization libraries
  ```bash
  npm install d3 @nivo/core @nivo/bar @nivo/line
  npm install plotly.js react-plotly.js
  ```

- [ ] Vytvořit `components/DataViz.tsx`
  ```typescript
  import { ResponsiveLine } from '@nivo/line';

  const DataViz = ({ data, type }) => {
      if (type === 'line') {
          return <ResponsiveLine data={data} />;
      }
      // Other viz types
  };
  ```

- [ ] Use cases:
  - [ ] Sports statistics (scores over time)
  - [ ] Movie ratings comparison
  - [ ] Music charts
  - [ ] News sentiment analysis

### 🎬 Media Components
- [ ] Enhanced `MediaViewer.tsx`
  ```typescript
  interface MediaViewerProps {
      type: 'image' | 'video' | 'audio';
      source: string;
      metadata?: any;
  }

  const MediaViewer: React.FC<MediaViewerProps> = ({ type, source, metadata }) => {
      switch (type) {
          case 'image':
              return <ImageGallery images={source} />;
          case 'video':
              return <ReactPlayer url={source} controls />;
          case 'audio':
              return <AudioPlayer src={source} />;
      }
  };
  ```

- [ ] Image gallery s lightbox
  ```bash
  npm install yet-another-react-lightbox
  ```

- [ ] Video player s controls
  - [ ] Play/pause
  - [ ] Volume
  - [ ] Fullscreen
  - [ ] Playback speed

### ⚡ Real-time Communication
- [ ] Upgrade WebSocket pro multiple message types
  ```typescript
  interface Message {
      type: 'text' | 'image' | 'video' | 'audio' | 'action';
      content: any;
      metadata?: {
          emotion?: string;
          timestamp?: number;
      };
  }

  ws.onmessage = (event) => {
      const message: Message = JSON.parse(event.data);
      handleMessage(message);
  };
  ```

- [ ] Implementovat typing indicators
- [ ] Implement message streaming (pro dlouhé LLM odpovědi)
- [ ] Add message reactions (thumbs up/down)

### 🎨 Theming & Animations
- [ ] Implement theme system
  ```typescript
  const themes = {
      light: {
          bg: '#ffffff',
          text: '#000000',
          primary: '#3b82f6',
      },
      dark: {
          bg: '#1a1a1a',
          text: '#ffffff',
          primary: '#8b5cf6',
      }
  };
  ```

- [ ] Smooth transitions (Framer Motion)
  ```bash
  npm install framer-motion
  ```

  ```typescript
  import { motion } from 'framer-motion';

  <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
  >
      Message content
  </motion.div>
  ```

- [ ] Add particle effects (optional, pro immersion)
- [ ] Custom cursor effects

---

## FÁZE 4: Vision & Camera (1 týden)

### 📷 Camera Integration
- [ ] Setup MediaPipe
  ```bash
  npm install @mediapipe/face_detection
  npm install @mediapipe/face_mesh
  ```

- [ ] Vytvořit `services/CameraService.ts`
  ```typescript
  import { FaceDetection } from '@mediapipe/face_detection';

  class CameraService {
      private faceDetection: FaceDetection;

      async initialize() {
          this.faceDetection = new FaceDetection({
              locateFile: (file) => {
                  return `https://cdn.jsdelivr.net/npm/@mediapipe/face_detection/${file}`;
              }
          });
      }

      async detectFace(videoElement: HTMLVideoElement) {
          await this.faceDetection.send({ image: videoElement });
      }
  }
  ```

- [ ] Vytvořit `components/CameraView.tsx`
  ```typescript
  const CameraView = () => {
      const videoRef = useRef<HTMLVideoElement>(null);

      useEffect(() => {
          navigator.mediaDevices.getUserMedia({ video: true })
              .then(stream => {
                  if (videoRef.current) {
                      videoRef.current.srcObject = stream;
                  }
              });
      }, []);

      return <video ref={videoRef} autoPlay />;
  };
  ```

- [ ] Privacy controls
  - [ ] Camera on/off toggle
  - [ ] Indicator when camera is active
  - [ ] Data retention policy info

### 👤 Face Detection & Tracking
- [ ] Implement face detection
  ```python
  # Backend
  import mediapipe as mp

  class FaceService:
      def __init__(self):
          self.face_detection = mp.solutions.face_detection.FaceDetection()

      async def detect_faces(self, image):
          results = self.face_detection.process(image)
          return results.detections
  ```

- [ ] Extract face embeddings (anonymní identifikace)
  ```python
  from facenet_pytorch import InceptionResnetV1

  class FaceEmbedder:
      def __init__(self):
          self.model = InceptionResnetV1(pretrained='vggface2').eval()

      async def get_embedding(self, face_crop):
          embedding = self.model(face_crop)
          return embedding.detach().numpy()
  ```

- [ ] Anonymous user tracking
  ```python
  # Store only embeddings, not images
  user_session = {
      "session_id": uuid.uuid4(),
      "face_embedding": embedding,  # 512-dim vector
      "first_seen": datetime.now(),
      "last_seen": datetime.now(),
      "conversation_count": 1
  }
  # Auto-delete after session ends
  ```

### 😊 Emotion Recognition
- [ ] Setup emotion detection model
  ```bash
  pip install fer
  # nebo use deeper model
  pip install deepface
  ```

- [ ] Implement emotion detection
  ```python
  from deepface import DeepFace

  class EmotionService:
      async def detect_emotion(self, face_image):
          result = DeepFace.analyze(
              face_image,
              actions=['emotion'],
              enforce_detection=False
          )
          return result['dominant_emotion']  # happy, sad, angry, etc.
  ```

- [ ] Use emotions to adapt response
  ```python
  async def generate_response(self, message, user_emotion):
      if user_emotion == "sad":
          system_prompt = "User seems sad. Be empathetic and supportive."
      elif user_emotion == "happy":
          system_prompt = "User seems happy. Match their energy."
      # ...
  ```

- [ ] Mirror emotions in avatar
  ```typescript
  // Frontend
  const [userEmotion, setUserEmotion] = useState('neutral');
  const [avatarEmotion, setAvatarEmotion] = useState('neutral');

  // Sync avatar emotion with user
  useEffect(() => {
      setAvatarEmotion(userEmotion);
  }, [userEmotion]);
  ```

### 🔮 Future: Scene Understanding (Prep)
- [ ] Research OWL-ViT (zero-shot object detection)
- [ ] Research Segment Anything Model (SAM)
- [ ] Plan integration architecture
- [ ] Note: Implement in Phase 2 nebo upgrade to Varianta C

---

## FÁZE 5: Dialog Management (2 týdny)

### 🧠 LangGraph State Machine
- [ ] Nainstalovat LangGraph
  ```bash
  pip install langgraph
  ```

- [ ] Design state machine
  ```python
  from langgraph.graph import StateGraph, END

  class DialogState(TypedDict):
      messages: List[Message]
      current_topic: Optional[str]
      user_emotion: Optional[str]
      context: Dict[str, Any]
      next_action: Optional[str]

  workflow = StateGraph(DialogState)

  # Add nodes
  workflow.add_node("understand", understand_intent)
  workflow.add_node("retrieve", retrieve_context)
  workflow.add_node("generate", generate_response)
  workflow.add_node("execute_action", execute_action)

  # Add edges
  workflow.add_edge("understand", "retrieve")
  workflow.add_edge("retrieve", "generate")
  workflow.add_conditional_edges(
      "generate",
      should_execute_action,
      {
          "action": "execute_action",
          "end": END
      }
  )
  ```

- [ ] Implement each node:

  **understand_intent:**
  ```python
  async def understand_intent(state: DialogState):
      user_message = state["messages"][-1]
      # Use LLM to classify intent
      intent = await intent_classifier.classify(user_message)
      # Detect topic
      topic = await topic_detector.detect(user_message)
      return {
          **state,
          "intent": intent,
          "current_topic": topic
      }
  ```

  **retrieve_context:**
  ```python
  async def retrieve_context(state: DialogState):
      topic = state["current_topic"]
      # RAG search
      context_docs = await rag.search(topic)
      # Web search if needed
      if should_search_web(state):
          web_results = await web_search(topic)
          context_docs.extend(web_results)
      return {
          **state,
          "context": {
              "docs": context_docs,
              "sources": [doc.metadata for doc in context_docs]
          }
      }
  ```

  **generate_response:**
  ```python
  async def generate_response(state: DialogState):
      # Build prompt with context
      prompt = build_prompt(
          messages=state["messages"],
          context=state["context"],
          user_emotion=state["user_emotion"]
      )
      # Generate
      response = await llm.generate(prompt)
      # Decide if action needed
      action = await action_planner.plan(response, state)
      return {
          **state,
          "messages": state["messages"] + [response],
          "next_action": action
      }
  ```

- [ ] Test state machine s různými scenarios

### 🎯 Action System
- [ ] Define action types
  ```python
  class ActionType(Enum):
      SHOW_IMAGE = "show_image"
      SHOW_VIDEO = "show_video"
      PLAY_MUSIC = "play_music"
      VISUALIZE_DATA = "visualize_data"
      SEARCH_WEB = "search_web"
      TELL_JOKE = "tell_joke"
      SHOW_AVATAR_EMOTION = "show_avatar_emotion"
  ```

- [ ] Implement action executor
  ```python
  class ActionExecutor:
      async def execute(self, action_type: ActionType, params: dict):
          if action_type == ActionType.SHOW_IMAGE:
              # Generate or fetch image
              image_url = await image_service.generate(params["prompt"])
              return {"type": "image", "url": image_url}

          elif action_type == ActionType.PLAY_MUSIC:
              # Generate music
              audio = await music_service.generate(params["description"])
              return {"type": "audio", "data": audio}

          # ... other actions
  ```

- [ ] Action planner (decide when to trigger actions)
  ```python
  class ActionPlanner:
      async def plan(self, response_text: str, state: DialogState):
          # Use LLM to decide
          prompt = f"""
          Given this response: {response_text}
          And conversation context: {state['context']}

          Should we take any action? If yes, which one?
          Respond with action type and parameters.
          """
          action_plan = await llm.generate(prompt)
          return self.parse_action(action_plan)
  ```

### 🗣️ Topic Management
- [ ] Implement topic tracking
  ```python
  class TopicTracker:
      def __init__(self):
          self.topics_discussed = []
          self.current_topic = None
          self.topic_start_time = None

      async def update(self, message: str):
          # Detect topic shift
          new_topic = await topic_detector.detect(message)
          if new_topic != self.current_topic:
              self.on_topic_change(new_topic)

      def on_topic_change(self, new_topic):
          # Log old topic
          if self.current_topic:
              self.topics_discussed.append({
                  "topic": self.current_topic,
                  "duration": time.time() - self.topic_start_time
              })
          # Update current
          self.current_topic = new_topic
          self.topic_start_time = time.time()
  ```

- [ ] Topic suggestions
  ```python
  async def suggest_topics(self, user_profile):
      # Based on past discussions
      interests = extract_interests(user_profile.topics_discussed)
      # Use RAG to find related topics
      suggestions = await rag.find_related_topics(interests)
      return suggestions
  ```

### 📝 Conversation Quality
- [ ] Implement engagement tracking
  ```python
  class EngagementTracker:
      metrics = {
          "avg_response_length": [],
          "response_times": [],
          "positive_reactions": 0,
          "negative_reactions": 0
      }

      def calculate_engagement_score(self):
          # Weighted score
          score = (
              0.3 * normalize(self.avg_response_length) +
              0.2 * (1 - normalize(self.response_times)) +
              0.5 * (self.positive / (self.positive + self.negative))
          )
          return score
  ```

- [ ] Implement conversation repair
  ```python
  async def detect_confusion(self, user_message):
      confusion_signals = [
          "what?", "i don't understand", "confused",
          "what do you mean", "unclear"
      ]
      if any(signal in user_message.lower() for signal in confusion_signals):
          return True
      return False

  async def repair_conversation(self, state):
      # Rephrase last response
      # Or change topic
      # Or ask clarifying question
      pass
  ```

---

## FÁZE 6: Integration & Testing (2 týdny)

### 🔗 End-to-End Integration
- [ ] Connect all services
  ```python
  # Main orchestrator
  class Almquist:
      def __init__(self):
          self.dialog_manager = DialogManager()
          self.llm_service = LLMService()
          self.rag_service = RAGService()
          self.tts_service = TTSService()
          self.image_service = ImageService()
          self.music_service = MusicService()
          self.camera_service = CameraService()
          self.action_executor = ActionExecutor()

      async def process_turn(self, user_input, camera_frame=None):
          # Full pipeline
          pass
  ```

- [ ] Implement request/response flow
  ```
  User Input (text/voice)
    ↓
  Intent Understanding
    ↓
  Context Retrieval (RAG)
    ↓
  LLM Generation
    ↓
  Action Planning
    ↓
  [Optional] Execute Actions (image/music/video)
    ↓
  Response (text + TTS + visuals)
    ↓
  Update State
  ```

- [ ] Test complete conversation flows

### 🧪 Testing Strategy
- [ ] **Unit Tests** (pytest)
  ```python
  # tests/test_rag_service.py
  @pytest.mark.asyncio
  async def test_rag_search():
      rag = RAGService()
      results = await rag.search("Avengers movie")
      assert len(results) > 0
      assert "Avengers" in results[0].content
  ```

- [ ] **Integration Tests**
  ```python
  # tests/test_dialog_flow.py
  @pytest.mark.asyncio
  async def test_movie_discussion():
      almquist = Almquist()
      response = await almquist.process_turn("Tell me about Inception")
      assert "movie" in response.lower()
      assert response.action_type == ActionType.SHOW_IMAGE
  ```

- [ ] **Performance Tests**
  ```python
  # tests/test_performance.py
  @pytest.mark.benchmark
  def test_llm_response_time():
      start = time.time()
      response = llm.generate("Hello")
      duration = time.time() - start
      assert duration < 0.5  # 500ms target
  ```

- [ ] **Frontend Tests** (Jest + Playwright)
  ```typescript
  // tests/e2e/chat.spec.ts
  test('user can send message and receive response', async ({ page }) => {
      await page.goto('http://localhost:3000');
      await page.fill('[data-testid="message-input"]', 'Hello');
      await page.click('[data-testid="send-button"]');
      await expect(page.locator('[data-testid="bot-message"]')).toBeVisible();
  });
  ```

### 🐛 Debugging & Profiling
- [ ] Setup logging
  ```python
  import logging
  from logging.handlers import RotatingFileHandler

  logger = logging.getLogger("almquist")
  logger.setLevel(logging.INFO)

  handler = RotatingFileHandler(
      "logs/almquist.log",
      maxBytes=10_000_000,
      backupCount=5
  )
  logger.addHandler(handler)
  ```

- [ ] Add performance monitoring
  ```python
  from functools import wraps
  import time

  def monitor_performance(func):
      @wraps(func)
      async def wrapper(*args, **kwargs):
          start = time.time()
          result = await func(*args, **kwargs)
          duration = time.time() - start
          logger.info(f"{func.__name__} took {duration:.2f}s")
          return result
      return wrapper
  ```

- [ ] Profile GPU usage
  ```python
  import pynvml

  pynvml.nvmlInit()
  handle = pynvml.nvmlDeviceGetHandleByIndex(0)

  def log_gpu_usage():
      info = pynvml.nvmlDeviceGetMemoryInfo(handle)
      logger.info(f"GPU Memory: {info.used / 1024**3:.2f} GB / {info.total / 1024**3:.2f} GB")
  ```

---

## FÁZE 7: Polish & Optimization (1 týden)

### ⚡ Performance Optimization
- [ ] Backend optimizations:
  - [ ] Implement request batching
  - [ ] Add Redis caching for RAG results
  - [ ] Optimize model loading (lazy loading)
  - [ ] Use async/await properly

- [ ] Frontend optimizations:
  - [ ] Code splitting (React.lazy)
  - [ ] Image lazy loading
  - [ ] Virtual scrolling for messages
  - [ ] WebWorkers pro heavy computations

- [ ] Benchmark improvements
  ```python
  # Before: 2.5s per turn
  # Target: < 1s per turn
  ```

### 🎨 UI/UX Polish
- [ ] User feedback session (5-10 users)
- [ ] Iterate based on feedback:
  - [ ] UI/UX improvements
  - [ ] Bug fixes
  - [ ] Feature tweaks

- [ ] Accessibility:
  - [ ] Keyboard navigation
  - [ ] Screen reader support (ARIA labels)
  - [ ] High contrast mode
  - [ ] Font size adjustment

- [ ] Error handling:
  - [ ] Graceful degradation
  - [ ] User-friendly error messages
  - [ ] Retry mechanisms
  - [ ] Offline mode (cache responses)

### 📊 Analytics & Monitoring
- [ ] Integrate with Grafana (tvůj existing stack!)
  ```python
  from prometheus_client import Counter, Histogram, Gauge

  requests_total = Counter('almquist_requests_total', 'Total requests')
  response_time = Histogram('almquist_response_seconds', 'Response time')
  gpu_usage = Gauge('almquist_gpu_usage_percent', 'GPU usage')
  ```

- [ ] Track key metrics:
  - [ ] Requests per minute
  - [ ] Average response time
  - [ ] Error rate
  - [ ] User satisfaction (ratings)
  - [ ] GPU/CPU utilization

- [ ] Setup alerts
  ```yaml
  # prometheus/alerts.yml
  - alert: HighResponseTime
    expr: almquist_response_seconds > 2
    annotations:
      summary: "Response time too high"
  ```

---

## FÁZE 8: Deployment (3-4 dny)

### 📦 Packaging
- [ ] Backend Docker images
  ```dockerfile
  # Dockerfile
  FROM nvidia/cuda:12.1-runtime-ubuntu22.04

  COPY requirements.txt .
  RUN pip install -r requirements.txt

  COPY . .

  CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
  ```

- [ ] Docker Compose prod config
  ```yaml
  version: '3.8'
  services:
      backend:
          build: ./backend
          deploy:
              resources:
                  reservations:
                      devices:
                          - driver: nvidia
                            count: 1
                            capabilities: [gpu]
      # ... other services
  ```

- [ ] Frontend Electron build
  ```bash
  npm run build:linux
  npm run build:windows  # cross-compile
  ```

### 🚀 Deployment Options
- [ ] **Option A: Single Machine** (tvůj workstation)
  ```bash
  docker-compose up -d
  # Run Electron app
  ./almquist-pro.AppImage
  ```

- [ ] **Option B: Local Network Server** (pokud máš víc strojů)
  - [ ] Deploy backend na server
  - [ ] Electron connects přes network
  - [ ] Multiple clients supported

### 📝 Documentation
- [ ] User manual:
  - [ ] Installation guide
  - [ ] First-time setup
  - [ ] Features overview
  - [ ] Troubleshooting

- [ ] Developer docs:
  - [ ] Architecture overview
  - [ ] API documentation
  - [ ] Adding new actions
  - [ ] Model updates

- [ ] Deployment guide:
  - [ ] System requirements
  - [ ] Installation steps
  - [ ] Configuration
  - [ ] Monitoring setup

---

## FÁZE 9: Alexa Prize Preparation (optional, 1-2 týdny)

### 📋 Competition Requirements
- [ ] Review SGC rules thoroughly
- [ ] Ensure compliance:
  - [ ] Multimodal support ✅
  - [ ] Conversation quality metrics
  - [ ] Privacy compliance
  - [ ] Scalability

### 🎯 Optimization for Metrics
- [ ] Focus on Alexa Prize KPIs:
  - [ ] **Average rating:** > 3.5/5
  - [ ] **Conversation length:** > 10 turns
  - [ ] **Coherence score:** > 0.8
  - [ ] **User retention:** > 40%

- [ ] Implement rating system
  ```python
  async def request_rating(self):
      # At end of conversation
      return "How would you rate this conversation? (1-5 stars)"
  ```

- [ ] Optimize for engagement:
  - [ ] Interesting topics
  - [ ] Proactive suggestions
  - [ ] Personality and humor
  - [ ] Timely media content

### 📊 Evaluation & Testing
- [ ] Internal testing (simulate competition)
  - [ ] Multiple testers
  - [ ] Various conversation scenarios
  - [ ] Collect ratings

- [ ] A/B testing different approaches:
  - [ ] Dialog strategies
  - [ ] Personality traits
  - [ ] Media usage frequency

### 📄 Submission Preparation
- [ ] Prepare technical paper:
  - [ ] System architecture
  - [ ] Novel contributions
  - [ ] Evaluation results
  - [ ] Lessons learned

- [ ] Video demonstration (required)
- [ ] Code repository cleanup
- [ ] Submit application!

---

## 🎯 Success Metrics

Po dokončení všech fází máš:

✅ Production-ready multimodal conversational AI
✅ 3D animated avatar with emotions
✅ Image generation (Stable Diffusion)
✅ Music generation (AudioCraft)
✅ Advanced RAG system (Qdrant)
✅ Camera integration + emotion detection
✅ Sophisticated dialog management (LangGraph)
✅ Data visualizations
✅ Monitoring & analytics
✅ Polished GUI (Electron + React + Three.js)
✅ Comprehensive documentation
✅ Ready for Alexa Prize submission

**Total estimated time:** 3-4 měsíce (300-400 hodin)

---

## 🆘 Risk Mitigation

### Potential Blockers:
1. **GPU Memory Issues**
   - Mitigation: Model quantization, reduce batch size
   - Fallback: Use smaller models (Llama 7B instead of 70B)

2. **Slow Image/Music Generation**
   - Mitigation: Pre-generate popular content
   - Fallback: Use online APIs as backup

3. **Complex 3D Avatar Performance**
   - Mitigation: LOD (level of detail), reduce polygons
   - Fallback: Use simpler 2D animated avatar

4. **Integration Issues**
   - Mitigation: Modular architecture, well-defined APIs
   - Fallback: Incremental integration, thorough testing

---

## 📚 Resources

### Key Documentation:
- LangGraph: https://github.com/langchain-ai/langgraph
- vLLM: https://docs.vllm.ai/
- Stable Diffusion: https://github.com/AUTOMATIC1111/stable-diffusion-webui
- AudioCraft: https://github.com/facebookresearch/audiocraft
- Three.js: https://threejs.org/docs/
- Ready Player Me: https://docs.readyplayerme.com/

### Papers to Study:
- Alquist 5.0 paper (arXiv:2310.16119)
- All Alexa Prize SGC5 winner papers
- Dialog State Tracking papers
- Multimodal learning papers

---

*Varianta B TODO vytvořen: 2025-11-24*
*Estimated completion: 3-4 měsíce*
*Recommended for Alexa Prize participation*
