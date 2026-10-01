.PHONY: help install install-dev cache api app test lint clean verify demo

PY      ?= python
PYTHONPATH := src
export PYTHONPATH

help:
	@grep -E '^[a-z-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-14s %s\n", $$1, $$2}'

install:      ## runtime deps for the API
	$(PY) -m pip install -r requirements-api.txt

install-dev:  ## everything, including tests and the client
	$(PY) -m pip install -r requirements-dev.txt

cache:        ## rebuild the cache (pinned seed -- ground rule 3)
	$(PY) -m qmems_cache.build_cache --days 10 --test-days 3 --seed 0

cache-demo:   ## small committed slice used by CI and offline fallback
	$(PY) -m qmems_cache.build_cache --cache-dir cache/demo --days 3 \
		--test-days 1 --seed 0 --tabular-episodes 300 \
		--methods dummy rule_based milp anticipative qubo_dp qubo_sa

api:          ## run the API on :8000  (docs at /docs)
	uvicorn qmems_api.main:app --reload --port 8000

app:          ## run the Streamlit client on :8501
	streamlit run app/streamlit_app.py

test:         ## full suite
	$(PY) -m pytest tests -q

lint:
	ruff check src app tests

verify:       ## checksum the cache against its manifest
	curl -s localhost:8000/api/v1/verify | $(PY) -m json.tool

demo:         ## cache + API + client, in that order
	$(MAKE) cache && $(MAKE) api

clean:
	rm -rf cache/_synthetic .pytest_cache **/__pycache__ .ruff_cache
