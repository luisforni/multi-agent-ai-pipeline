# Multi-Agent AI Pipeline

Pipeline de inteligencia artificial compuesto por tres agentes especializados que investigan, resumen y generan contenido sobre cualquier tema. Los agentes se coordinan mediante CrewAI o LangGraph y exponen una API REST por FastAPI. Un dashboard Next.js permite interactuar con el sistema desde el navegador.

## Arquitectura

```
pipeline-web-ui  (Next.js · puerto 3010)
       │
       ▼
agent-orchestrator  (FastAPI · puerto 9000)
       │
       ├──▶ agent-researcher      (FastAPI · puerto 9001)
       │         └── DuckDuckGo / Tavily + BeautifulSoup
       │
       ├──▶ agent-summarizer      (FastAPI · puerto 9002)
       │
       └──▶ agent-content-generator  (FastAPI · puerto 9003)
```

## Repositorios

| Repositorio | Descripción |
|---|---|
| `multi-agent-ai-pipeline` | Monorepo raíz — Docker Compose, configuración compartida |
| `agent-researcher` | Agente de investigación con búsqueda web y scraping |
| `agent-summarizer` | Agente de resumen con tres estilos configurables |
| `agent-content-generator` | Agente generador de contenido (blog, reporte, redes sociales) |
| `agent-orchestrator` | Orquestador CrewAI/LangGraph y punto de entrada del pipeline |
| `pipeline-web-ui` | Dashboard Next.js para interactuar con el pipeline |

## Proveedores LLM soportados

| `LLM_PROVIDER` | Modelo por defecto |
|---|---|
| `openai` | gpt-4o |
| `anthropic` | claude-opus-4-6 |
| `groq` | llama-3.3-70b-versatile |
| `ollama` | llama3 (local) |

## Inicio rápido

**Requisitos:** Docker, Docker Compose y API key del proveedor elegido.

```bash
cp .env.example .env
# Editar .env: establecer LLM_PROVIDER y la API key correspondiente
docker compose up -d --build
```

Abrir el dashboard en `http://localhost:3010`.

## Comandos

```bash
make up                                   # Iniciar todos los servicios
make down                                 # Detener todos los servicios
make build                                # Reconstruir imágenes Docker
make logs                                 # Ver logs en tiempo real
make test                                 # Verificar health de los servicios
make run-pipeline TOPIC="tu tema"         # Ejecutar pipeline desde terminal
make dev-ui                               # Ejecutar frontend en modo desarrollo
make up-ollama                            # Iniciar con soporte Ollama local
```

## API

### `POST /pipeline/run`

```json
{
  "topic": "inteligencia artificial en 2025",
  "content_format": "blog",
  "summary_style": "bullets",
  "language": "es",
  "engine": "crewai"
}
```

| Campo | Valores | Por defecto |
|---|---|---|
| `content_format` | `blog`, `report`, `social` | `blog` |
| `summary_style` | `bullets`, `narrative`, `technical` | `bullets` |
| `engine` | `crewai`, `langgraph` | `crewai` |
| `language` | código ISO (en, es, pt, fr, de…) | `en` |

## Estructura

```
multi-agent-ai-pipeline/
├── shared/
│   ├── config.py            # Configuración centralizada desde variables de entorno
│   └── llm_factory.py       # Fábrica de modelos LLM para LangChain y CrewAI
├── agent-researcher/        # Submodule
├── agent-summarizer/        # Submodule
├── agent-content-generator/ # Submodule
├── agent-orchestrator/      # Submodule
├── pipeline-web-ui/         # Submodule
├── docker-compose.yml
├── .env.example
└── Makefile
```

## Tecnologías

| Framework | Rol |
|---|---|
| CrewAI | Orquestación de agentes con roles, objetivos y tareas encadenadas |
| LangChain | Abstracción de modelos LLM y herramientas |
| LangGraph | Pipeline alternativo con estado persistente y reanudable |
| FastAPI | API REST por agente |
| Next.js | Dashboard web |
| Docker Compose | Orquestación de contenedores |
