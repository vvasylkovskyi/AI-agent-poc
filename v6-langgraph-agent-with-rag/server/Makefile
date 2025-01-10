.PHONY: install run test clean

install:
	poetry install

run:
	poetry run uvicorn main:app --reload

test:
	poetry run pytest

clean:
	find . -type d -name __pycache__ -exec rm -r {} +