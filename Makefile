.PHONY: help install test lint clean

PYTHON          ?= python3
PROJECT_NAME    := ldapsm
SRC_DIR         := src
TEST_DIR        := tests

help:
	@echo "Available targets:"
	@echo "  install   Install project in editable mode"
	@echo "  test      Run unit tests"
	@echo "  clean     Remove Python cache files"

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e .

test:
	$(PYTHON) -m unittest discover -s $(TEST_DIR) -p "test_*.py"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
