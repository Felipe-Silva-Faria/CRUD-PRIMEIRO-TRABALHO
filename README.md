# Versão 3.0 (Sprint 4): o que muda no projeto

A S4 entra **por cima** do que S1, S2 e S3 construíram. Nenhum arquivo antigo é apagado:
3 são **alterados** (só com acréscimos), o `main.py` antigo vira `main_classico.py` e o resto é **novo**.

## 1. Mapa: o que cada sprint deixou e o que a S4 acrescenta

| Já existia (S1–S3) | Como a S4 usa | Arquivo novo ou alterado |
|---|---|---|
| `dominio/` (entidades, enums, validação, exceções) | Continua sendo o domínio oficial. Toda validação da tela nova passa por ele | — |
| `algoritmos/cvss.py` | O campo CVSS da tela nova usa `interpretar_entrada` e `descrever_vetor` | — |
| `algoritmos/risco.py` (álgebra S3_09–S3_12) | A página **Riscos** mostra b = Mv, (I − A)x = b, det, κ e ρ(A) | — |
| `persistencia/dependencias.py` | As mesmas dependências viram as **arestas do grafo** (BFS/DFS) | `estruturas/grafo.py` |
| `persistencia/repositorio.py` (SQLite com FK) | `RelatorioSQL` **herda** do `RepositorioSQLite` e só acrescenta as consultas | `persistencia/relatorios_sql.py` |
| `algoritmos/ordenacao.py` (5 algoritmos, `ALGORITMOS`) | Ganha merge bottom-up e quick sort de Hoare; a tela escolhe pelo nome (Strategy) | **alterado** |
| `algoritmos/busca.py` (`indexar` com dict) | A S4 implementa a tabela hash "na mão" para a busca da tela | `estruturas/tabela_hash.py` |
| — | Árvore binária para o filtro "CVSS ≥ x" | `estruturas/arvore_bst.py` |
| `servicos/servico_ativos.py` | É a fonte do modo local; a tela usa as `CHAVES_ORDENACAO` dele | `servicos/painel.py` (Facade + Adapter) |
| `api/cliente_api.py` (fila offline) | É a fonte padrão da tela nova: online/offline e sincronização continuam iguais | — |
| `api/app_rest.py` | Ganha middleware de log, chave de API opcional e versão 3.0.0 | **alterado** |
| `utilitarios/log.py` (`crud.log`) | Continua; a S4 acrescenta `crud.jsonl` com rotação e eventos de segurança | `utilitarios/auditoria.py` |
| `analise/benchmark.py` | Ganha a seção hash × dict e altura da BST | **alterado** |
| `interface/janela_*.py`, `ativos/`, `estado.py` | **Continuam funcionando**: `python main.py --classica` | — |
| `config.py` (cores, `ARQUIVO_TXT`, `URL_API`) | A tela nova usa as mesmas cores e os mesmos caminhos | — |
| `tests/` (254 testes) | **Todos continuam**; os novos ficam em `tests/test_s4_*.py` | 5 arquivos novos |
| — | Login com PBKDF2 e usuários em JSON | `servicos/autenticacao.py`, `persistencia/usuarios.py` |
| — | Observer para as telas se atualizarem | `servicos/eventos.py` |
| — | Interface moderna (8 páginas) | `interface/moderna/` |
| — | Docker, Compose e Linux | `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `requirements-docker.txt`, `deploy/` |

## 2. Passo a passo (PowerShell, pasta `CRUD-2.0`)

### 2.1 Guardar a 2.x numa branch própria

```powershell
cd C:\Users\RFSDY\PycharmProjects\CRUD-2.0
git checkout main
git pull origin main
git checkout -b versao-2.x
git push -u origin versao-2.x
```

Essa branch fica como registro da entrega da S3 (tag `v2.1`). Correções da 2.x são feitas nela.

### 2.2 Abrir a branch da 3.0 a partir da `develop`

```powershell
git checkout develop
git pull origin develop
git merge main
git checkout -b feature/v3.0-s4
```

### 2.3 Guardar o `main.py` antigo (antes de extrair o zip)

```powershell
git mv main.py main_classico.py
git commit -m "Interface antiga preservada como main_classico.py"
```

### 2.4 Copiar os arquivos da 3.0

```powershell
Expand-Archive "$env:USERPROFILE\Downloads\crud_v3_comentado.zip" -DestinationPath ..\crud_v3 -Force
Copy-Item -Recurse -Force ..\crud_v3\* .
Copy-Item -Force ..\crud_v3\.dockerignore .
git status
```

O `git status` precisa mostrar **só**:
- `modified:` `algoritmos/ordenacao.py`, `analise/benchmark.py`, `api/app_rest.py`;
- arquivos novos (`estruturas/tabela_hash.py`, `interface/moderna/`, `tests/test_s4_*.py`, `main.py`...).

Se aparecer **qualquer outro `modified`** ou algum `deleted`, pare e me mande a saída.

### 2.5 `.gitignore` e dependências

```powershell
Add-Content .gitignore "`nusuarios.json`npreferencias_interface.json"
pip install -r requirements-dev.txt
pip install numpy
```

`usuarios.json` guarda o hash das senhas e não deve ir para o GitHub.

### 2.6 Testar

```powershell
python -m pytest -q
ruff check .
python main.py --local
```

- **pytest:** o esperado é **308 passed**: os 254 de antes, 36 novos em `tests/test_s4_*.py` e 18 casos a mais no `test_algoritmos.py`, que já testa automaticamente todo algoritmo registrado em `ALGORITMOS` (os 2 novos entram sozinhos).
- **ruff:** se acusar algo nos arquivos novos, `ruff check . --fix` e me mande o que sobrar.
- **Janela:** abre no "Primeiro acesso" para criar o administrador.
- **Interface antiga:** `python main.py --classica`.

### 2.7 Commit por grupo de cartões

```powershell
git add estruturas algoritmos/ordenacao.py analise/benchmark.py tests/test_s4_estruturas.py
git commit -m "S4_08-S4_13: tabela hash, BST, grafo, merge bottom-up, quick de Hoare e benchmark"
git add persistencia servicos utilitarios/auditoria.py api/app_rest.py tests/test_s4_*.py
git commit -m "S4_01-S4_07, S4_18: fachada, observer, login, relatorios SQL e logs JSON"
git add interface/moderna main.py .gitignore
git commit -m "S4: interface moderna (8 paginas)"
git add Dockerfile docker-compose.yml .dockerignore requirements-docker.txt deploy LEIA-ME_V3.md
git commit -m "S4_15-S4_20: Docker, Compose e implantacao Linux"
git push -u origin feature/v3.0-s4
```

### 2.8 Levar para `develop` e `main` com a tag `v3.0`

```powershell
git checkout develop
git merge --no-ff feature/v3.0-s4
git push origin develop
git checkout main
git pull origin main
git merge --no-ff develop -m "Release v3.0: Sprint 4"
git tag -a v3.0 -m "Versao 3.0 - Sprint 4"
git push origin main
git push origin v3.0
git checkout develop
```

## 3. Como rodar

| Comando | O que faz |
|---|---|
| `python main.py` | Interface nova usando a API (cai para o `banco_ativos.txt` se ela estiver fora, como na S3) |
| `python main.py --local` | Interface nova só com o arquivo local |
| `python main.py --classica` | Janelas antigas |
| `python -m uvicorn api.app_rest:app --reload` | API, como antes |
| `python -m analise.benchmark` | Benchmark da S2 + seção da S4 |
| `docker compose up -d --build` | API no container (porta 8000, só localhost) |
| `docker compose --profile testes run --rm testes` | pytest dentro do container |

**Chave da API (opcional):** defina `$env:CRUD_API_KEY = "uma-frase-longa"` **nos dois terminais** (API e interface). Sem a variável, tudo funciona como na 2.1.

## 4. O que a tela nova não tem (e por quê)

- **Gráfico por mês:** o domínio não guarda data de cadastro. No lugar, o Dashboard mostra a distribuição por nota CVSS.
- **Login com GitHub/Windows, anexos e notificações do mockup:** não funcionariam de verdade num projeto local.
