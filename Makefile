PYTHON ?= .venv/bin/python
export PYTHONPATH := src

.PHONY: venv test

venv:
	uv venv --python 3.11 .venv
	uv pip install --python .venv --require-hashes -r requirements.txt -r requirements-dev.txt

test:
	$(PYTHON) -m pytest -q

.PHONY: validar
validar:
	$(PYTHON) -m vitral.validate --anos $(or $(ANOS),1) $(if $(ANO),--ano $(ANO),)

.PHONY: calendario livro site publicar-simulado
calendario:  ## lista os dias e as chaves do Lecionário: make calendario ANO=2026
	$(PYTHON) -m vitral.listar --ano $(ANO) --leituras

livro:  ## gera PDF, EPUB e AZW3 em dist/: make livro ANO=2026
	$(PYTHON) -m vitral.build --ano $(ANO)

site:  ## gera o site estático em site/out (lê dist/catalog.json se existir)
	cd site && npm ci && VITRAL_CATALOG=../dist/catalog.json npm run build

publicar-simulado:  ## roda a lógica de publicação sem falar com o GitHub
	$(PYTHON) scripts/publish.py --simular
