.PHONY: install run test clean evaluate

install:
	poetry install

run:
	poetry run uvicorn main:app --reload

evaluate:
	poetry run python -m evaluation.evaluation
test:
	poetry run pytest

clean:
	find . -type d -name __pycache__ -exec rm -r {} +