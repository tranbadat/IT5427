.PHONY: help install setup docker-up docker-down clean test lint format run-etl run-api run-dashboard

help:
	@echo "Available commands:"
	@echo "  make install       - Install Python dependencies"
	@echo "  make setup         - Initialize project (create directories, download models)"
	@echo "  make docker-up     - Start all Docker services"
	@echo "  make docker-down   - Stop all Docker services"
	@echo "  make clean         - Clean temporary files"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linter"
	@echo "  make format        - Format code"
	@echo "  make run-etl       - Run ETL pipeline"
	@echo "  make run-api       - Run FastAPI server"
	@echo "  make run-dashboard - Run Dash dashboard"
	@echo "  make run-stream    - Run streaming processor"

install:
	pip install -r requirements.txt

setup:
	mkdir -p data/raw data/processed data/output logs
	mkdir -p configs/clickhouse
	python -m spacy download en_core_web_sm
	python -m nltk.downloader punkt stopwords vader_lexicon

docker-up:
	docker-compose up -d
	@echo "Waiting for services to start..."
	sleep 30
	python scripts/init_databases.py

docker-down:
	docker-compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov

test:
	pytest tests/ -v --cov=src --cov-report=html

lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/
	isort src/ tests/

run-etl:
	python src/main_etl.py

run-api:
	uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

run-dashboard:
	python src/dashboard/app.py

run-stream:
	python src/streaming/stream_processor.py

run-all:
	@echo "Starting all services..."
	make docker-up
	python src/main_etl.py &
	python src/streaming/stream_processor.py &
	python src/api.main:app &
	python src/dashboard/app.py
