.PHONY: install run test clean langgraph

install:
	poetry install

run:
	poetry run uvicorn app.main:app --reload

test:
	poetry run pytest

clean:
	find . -type d -name __pycache__ -exec rm -r {} +

langgraph:
	poetry run langgraph dev