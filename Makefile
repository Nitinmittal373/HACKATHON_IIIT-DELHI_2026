# One command for the API contract: backend model -> contracts/openapi.json -> frontend types.
# Needs the backend dependencies installed (pip install -r backend/requirements-dev.txt) and
# `npm ci` run in frontend/.

PYTHON ?= python

.PHONY: contract
contract:
	cd backend && $(PYTHON) -m scripts.export_openapi
	cd frontend && npm run gen:api
