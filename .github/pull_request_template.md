## O que este PR faz


## Card do Trello


## Tipo de mudanca
- [ ] Nova funcionalidade
- [ ] Correcao de bug
- [ ] Refatoracao (sem mudar comportamento)
- [ ] Testes / CI / documentacao

## Como testar
1. `pytest -q`
2. `uvicorn api.app_rest:app --reload`
3. `python main.py`

## Checklist
- [ ] Criei a branch a partir de `develop` (`feature/...` ou `fix/...`)
- [ ] `ruff check .` sem erros
- [ ] `pytest` passando localmente
- [ ] Adicionei/atualizei testes para o que mudou
- [ ] Nao subi `.venv`, `.idea`, `__pycache__`, `banco_*.txt/.db` ou `logs/`
