.PHONY: help up down logs build dev-install run-pipeline test

PROVIDER ?= openai

help:
	@echo "Multi-Agent AI Pipeline"
	@echo ""
	@echo "  make up              Start all services (Docker)"
	@echo "  make up-ollama       Start all services + local Ollama"
	@echo "  make down            Stop all services"
	@echo "  make logs            Follow all service logs"
	@echo "  make build           Rebuild Docker images"
	@echo "  make dev-install     Install deps locally for development"
	@echo "  make dev-ui          Run Next.js frontend in dev mode"
	@echo "  make run-pipeline    Run full pipeline (topic via TOPIC=...)"
	@echo ""
	@echo "  PROVIDER=groq make up   Change LLM provider"
	@echo "  open http://localhost:3000   Access the web UI"

up:
	docker compose up -d

up-ollama:
	docker compose -f docker-compose.yml -f docker-compose.ollama.yml up -d

down:
	docker compose down

logs:
	docker compose logs -f

build:
	docker compose build --no-cache

dev-install:
	pip install -r agent-orchestrator/requirements.txt
	pip install -r agent-researcher/requirements.txt
	pip install -r agent-summarizer/requirements.txt
	pip install -r agent-content-generator/requirements.txt
	cd pipeline-web-ui && npm install

dev-ui:
	cd pipeline-web-ui && npm run dev

run-pipeline:
	@echo "Running pipeline for topic: $(TOPIC)"
	curl -s -X POST http://localhost:9000/pipeline/run \
		-H "Content-Type: application/json" \
		-d '{"topic": "$(TOPIC)"}' | python3 -m json.tool

test:
	curl -s http://localhost:9000/health | python3 -m json.tool
	curl -s http://localhost:9001/health | python3 -m json.tool
	curl -s http://localhost:9002/health | python3 -m json.tool
	curl -s http://localhost:9003/health | python3 -m json.tool
	@echo "Web UI → http://localhost:3000"
