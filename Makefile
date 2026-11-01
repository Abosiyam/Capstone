# ============================================================================
# Makefile – Standardized commands for the Boréal Marché project
# ============================================================================

setup:
	pip install -r requirements.txt

etl:
	python src/data_cleaning.py

rules:
	cd src && python recommendation.py
	cd src && python recommendation_engine.py

train:
	cd src && python sagemaker_train.py

index:
	cd src && python build_tfidf_index.py

test:
	pytest tests/ -v

up:
	docker compose up --build -d

down:
	docker compose down