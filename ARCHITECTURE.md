# Arquitectura del Sistema

Este documento describe el flujo exacto de ejecución cuando el usuario hace clic en **Run pipeline** en el dashboard web, con detalle de cada archivo, clase y función involucrada.

---

## Visión general

```
Navegador
   │  POST /api/pipeline/run  {"topic": "...", "engine": "crewai", ...}
   ▼
pipeline-web-ui / src/app/api/pipeline/run/route.ts
   │  POST http://orchestrator:9000/pipeline/run
   ▼
agent-orchestrator / src/api.py  →  run_pipeline()
   │
   ├── engine = "crewai"  →  src/crew.py  →  run_pipeline_crewai()
   │       │
   │       ├── Agente 1: Senior Research Analyst
   │       │       └── tools: web_search(), scrape_webpage()
   │       │
   │       ├── Agente 2: Expert Content Summarizer
   │       │
   │       └── Agente 3: Creative Content Writer
   │
   └── engine = "langgraph"  →  src/graph.py  →  run_pipeline_graph()
           │
           ├── research_node()
           ├── summarize_node()
           └── generate_content_node()
```

---

## Paso 1 — El usuario hace clic en "Run pipeline"

**Archivo:** `pipeline-web-ui/src/app/page.tsx`

**Función:** `handleRun(params: PipelineParams)`

El componente `Home` es un client component de Next.js. Cuando el usuario hace clic en el botón, se ejecuta `handleRun`:

1. Establece `loading = true` y limpia el estado anterior (`error`, `result`)
2. Realiza un `fetch` con método `POST` a `/api/pipeline/run`
3. El body es el objeto `PipelineParams` serializado a JSON:
   ```json
   {
     "topic": "...",
     "content_format": "blog",
     "summary_style": "bullets",
     "language": "es",
     "engine": "crewai"
   }
   ```
4. Espera la respuesta. Si el status no es OK, lanza un error con el body
5. En caso de éxito, guarda el resultado en `setResult(data)` para renderizar el `ResultPanel`
6. Siempre ejecuta `setLoading(false)` en el bloque `finally`

---

## Paso 2 — Proxy server-side al orchestrator

**Archivo:** `pipeline-web-ui/src/app/api/pipeline/run/route.ts`

**Función:** `POST(request: NextRequest)`

Esta es una API Route de Next.js que se ejecuta en el servidor (no en el navegador). Su propósito es evitar problemas de CORS y resolver la URL del orchestrator en runtime desde la variable de entorno.

1. Lee `process.env.ORCHESTRATOR_URL` (en Docker = `http://orchestrator:9000`)
2. Extrae el body JSON de la petición entrante
3. Hace un `fetch` al orchestrator: `POST http://orchestrator:9000/pipeline/run`
4. Devuelve la respuesta del orchestrator al cliente con el mismo status HTTP

---

## Paso 3 — Recepción y despacho en el orchestrator

**Archivo:** `agent-orchestrator/src/api.py`

**Función:** `run_pipeline(req: PipelineRequest)`

FastAPI recibe la petición en el endpoint `POST /pipeline/run`.

**Clase `PipelineRequest`** (Pydantic):
- `topic: str` — mínimo 3 caracteres, requerido
- `content_format: Literal["blog", "report", "social"]` — por defecto `"blog"`
- `summary_style: Literal["bullets", "narrative", "technical"]` — por defecto `"bullets"`
- `language: str` — código ISO, por defecto `"en"`
- `engine: Literal["crewai", "langgraph"]` — por defecto `"crewai"`

La función `run_pipeline`:
1. Valida que `topic` no esté vacío
2. Registra el timestamp de inicio con `time.time()`
3. Despacha al motor seleccionado:
   - `engine == "crewai"` → importa y llama `run_pipeline_crewai()`
   - `engine == "langgraph"` → importa y llama `run_pipeline_graph()`
4. Calcula `elapsed_seconds`
5. Construye y devuelve un `PipelineResponse` con `research`, `summary`, `content` y metadata

---

## Paso 4A — Motor CrewAI

**Archivo:** `agent-orchestrator/src/crew.py`

**Función:** `run_pipeline_crewai(topic, content_format, summary_style, language)`

### Creación del LLM

Llama a `get_crewai_llm()` de `shared/llm_factory.py`, que devuelve un string LiteLLM del formato `"proveedor/modelo"` (p.ej. `"groq/llama-3.3-70b-versatile"`). CrewAI usa LiteLLM internamente para hacer las llamadas al API.

### Agente 1: Senior Research Analyst

```python
researcher = Agent(
    role="Senior Research Analyst",
    tools=[web_search, scrape_webpage],
    llm=llm,
    max_iter=settings.RESEARCHER_MAX_ITER,
)
```

Las herramientas `web_search` y `scrape_webpage` están definidas en `agent_researcher/src/tools.py` con el decorador `@tool` de CrewAI.

### Agente 2: Expert Content Summarizer

```python
summarizer = Agent(
    role="Expert Content Summarizer",
    tools=[],
    llm=llm,
)
```

No usa herramientas externas. Opera solo con el contexto de la tarea anterior.

### Agente 3: Creative Content Writer

```python
generator = Agent(
    role="Creative Content Writer",
    tools=[],
    llm=llm,
)
```

### Tareas encadenadas

```python
research_task  = Task(agent=researcher, ...)
summarize_task = Task(agent=summarizer, context=[research_task], ...)
content_task   = Task(agent=generator,  context=[summarize_task], ...)
```

El parámetro `context=[prev_task]` hace que CrewAI inyecte automáticamente el output de la tarea anterior en el prompt de la siguiente.

### Ejecución

```python
crew = Crew(agents=[...], tasks=[...], process=Process.sequential)
crew.kickoff()
```

CrewAI ejecuta las tres tareas en orden. Al finalizar, cada `Task` tiene su `output.raw` con el resultado.

---

## Paso 4B — Motor LangGraph

**Archivo:** `agent-orchestrator/src/graph.py`

**Función:** `run_pipeline_graph(topic, content_format, summary_style, language)`

### Estado compartido

**Clase `PipelineState`** (TypedDict):
```python
class PipelineState(TypedDict):
    topic: str
    content_format: str
    summary_style: str
    language: str
    research: str
    summary: str
    content: str
    messages: Annotated[list[BaseMessage], operator.add]
```

El campo `messages` usa `operator.add` como reducer, lo que significa que los mensajes se acumulan entre nodos en lugar de reemplazarse.

### Nodo 1: `research_node(state)`

1. Obtiene el LLM con `get_llm()` (LangChain)
2. Vincula las herramientas al LLM: `llm.bind_tools([web_search, scrape_webpage])`
3. Construye un `ChatPromptTemplate` con el rol de Research Analyst
4. Invoca la cadena `prompt | llm_with_tools`
5. Si el LLM devuelve `tool_calls`, `_execute_tool_calls()` ejecuta cada herramienta y hace una segunda llamada al LLM con los resultados
6. Devuelve el estado actualizado con `research = resultado`

### Función auxiliar: `_execute_tool_calls(response, llm, topic)`

Si la respuesta del LLM contiene llamadas a herramientas (`response.tool_calls`):
1. Ejecuta cada herramienta llamando a su función directamente
2. Construye los mensajes con los resultados
3. Hace una segunda llamada al LLM incluyendo los resultados de las herramientas
4. Devuelve el texto final

### Nodo 2: `summarize_node(state)`

1. Toma `state["research"]` como entrada
2. Construye un prompt con las instrucciones de estilo del resumen
3. Invoca el LLM directamente (sin herramientas)
4. Devuelve el estado actualizado con `summary = resultado`

### Nodo 3: `generate_content_node(state)`

1. Toma `state["summary"]` y `state["topic"]` como entrada
2. Construye un prompt con la especificación del formato de contenido
3. Invoca el LLM
4. Devuelve el estado actualizado con `content = resultado`

### Construcción y ejecución del grafo

```python
graph = StateGraph(PipelineState)
graph.add_node("research", research_node)
graph.add_node("summarize", summarize_node)
graph.add_node("generate_content", generate_content_node)
graph.add_edge(START, "research")
graph.add_edge("research", "summarize")
graph.add_edge("summarize", "generate_content")
graph.add_edge("generate_content", END)
app = graph.compile()
final_state = app.invoke(initial_state)
```

---

## Paso 5 — Herramientas de investigación

**Archivo:** `agent-researcher/src/tools.py`

### `web_search(query, max_results=5)`

Decorada con `@tool` de CrewAI. Lógica:
1. Lee `TAVILY_API_KEY` del entorno
2. Si la key existe → llama a `_tavily_search()`: hace `POST https://api.tavily.com/search` con httpx
3. Si no → llama a `_ddg_search()`: usa la librería `duckduckgo-search` con `DDGS().text()`
4. Devuelve los resultados formateados como string Markdown con título, URL y snippet

### `scrape_webpage(url)`

Decorada con `@tool` de CrewAI. Lógica:
1. Hace `GET` a la URL con `requests` y `User-Agent` personalizado
2. Parsea el HTML con `BeautifulSoup`
3. Elimina etiquetas de ruido: `script`, `style`, `nav`, `footer`, `header`, `aside`
4. Extrae texto plano con `get_text(separator="\n")`
5. Colapsa líneas en blanco repetidas con regex
6. Devuelve los primeros 3000 caracteres

---

## Paso 6 — Configuración y fábrica de LLM

**Archivo:** `shared/config.py`

**Clase `Settings`:** Lee todas las variables de entorno al importar. Valores relevantes:
- `LLM_PROVIDER`, `LLM_MODEL` — proveedor y modelo activos
- `_PROVIDER_DEFAULTS` — modelo por defecto por proveedor
- `get_model()` — devuelve `LLM_MODEL` si está definido, o el default del proveedor

**Archivo:** `shared/llm_factory.py`

| Función | Uso | Retorno |
|---|---|---|
| `get_llm(provider, model, temperature)` | LangChain (LangGraph, agentes individuales) | `BaseChatModel` (ChatOpenAI / ChatAnthropic / ChatGroq / ChatOllama) |
| `get_crewai_llm(provider, model)` | CrewAI >= 0.80 | `str` en formato LiteLLM: `"groq/llama-3.3-70b-versatile"` |

---

## Paso 7 — Respuesta al navegador

El orchestrator devuelve el `PipelineResponse` serializado a JSON. El proxy en Next.js lo reenvía al cliente. El componente `handleRun` almacena el resultado en el estado de React.

El componente `ResultPanel` (`pipeline-web-ui/src/components/ResultPanel.tsx`) renderiza:
- Barra de metadata: estado (`Pipeline complete`), motor utilizado, tema
- Tres pestañas: **Research**, **Summary**, **Content**
- El contenido de la pestaña activa en un `<pre>` con estilos Tailwind
- Botón de copia al portapapeles para la pestaña activa

---

## Resumen de archivos por capa

| Capa | Archivo | Responsabilidad |
|---|---|---|
| Frontend | `pipeline-web-ui/src/app/page.tsx` | Estado, formulario, llamada al API, renderizado de resultados |
| Frontend | `pipeline-web-ui/src/components/PipelineForm.tsx` | Formulario controlado con todos los parámetros del pipeline |
| Frontend | `pipeline-web-ui/src/components/ResultPanel.tsx` | Panel de resultados con pestañas y copia |
| Proxy | `pipeline-web-ui/src/app/api/pipeline/run/route.ts` | Proxy server-side al orchestrator |
| API Gateway | `agent-orchestrator/src/api.py` | Validación, despacho al motor, respuesta |
| Motor CrewAI | `agent-orchestrator/src/crew.py` | Pipeline secuencial con 3 agentes CrewAI |
| Motor LangGraph | `agent-orchestrator/src/graph.py` | Pipeline stateful con StateGraph |
| Herramientas | `agent-researcher/src/tools.py` | Búsqueda web y scraping de páginas |
| Config | `shared/config.py` | Variables de entorno centralizadas |
| LLM Factory | `shared/llm_factory.py` | Instanciación de modelos LangChain y strings LiteLLM |
