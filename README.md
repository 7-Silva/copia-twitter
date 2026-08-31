# Pamps 🐦

Uma API REST de posts estilo Twitter, construída com **FastAPI** e **PostgreSQL**, com autenticação JWT (access + refresh token), relacionamentos entre usuários e posts (incluindo respostas encadeadas) e ambiente 100% containerizado com Docker.

> Projeto desenvolvido para estudo e prática de arquitetura de APIs modernas em Python, com foco em boas práticas de desenvolvimento, versionamento de schema e configuração por ambiente.

---

## ✨ Stack técnica

| Camada | Tecnologia |
|---|---|
| Framework web | [FastAPI](https://fastapi.tiangolo.com/) |
| ORM / Modelagem de dados | [SQLModel](https://sqlmodel.tiangolo.com/) (Pydantic + SQLAlchemy) |
| Banco de dados | PostgreSQL 14 (Alpine) |
| Migrações de schema | Alembic |
| Autenticação | JWT (access + refresh token) via `python-jose` |
| Hash de senha | Passlib + Bcrypt |
| Configuração | Dynaconf (múltiplos ambientes: development / production / testing) |
| CLI administrativa | Typer + Rich |
| Testes | Pytest + HTTPX (TestClient do FastAPI) |
| Dados fictícios para desenvolvimento | Faker |
| Containerização | Docker + Docker Compose (multi-container: API + banco) |
| Servidor ASGI | Uvicorn (com hot-reload em desenvolvimento) |

---

## 🏗️ Arquitetura

```
pamps/
├── app.py          # Instância da aplicação FastAPI
├── auth.py         # Autenticação JWT (access/refresh tokens, dependências de segurança)
├── security.py     # Hash e verificação de senha (bcrypt)
├── config.py       # Configuração via Dynaconf (default.toml + settings.toml + .secrets.toml)
├── db.py           # Engine do SQLAlchemy e injeção de sessão
├── cli.py          # Comandos administrativos (criação de usuários, shell interativo, etc.)
├── models/
│   ├── user.py     # Model de usuário + schemas de request/response
│   └── post.py     # Model de post (com auto-relacionamento para respostas)
└── routes/
    ├── auth.py     # /token, /refresh_token
    ├── user.py     # CRUD de usuários
    └── post.py     # CRUD de posts + respostas encadeadas

migrations/         # Versionamento de schema via Alembic
postgres/           # Dockerfile customizado do Postgres (suporte a múltiplos bancos)
```

**Decisões de design que valem destaque:**

- **Separação entre modelo de tabela e schema de API**: cada entidade tem um `Model` (SQLModel, mapeado pro banco) e schemas dedicados de entrada/saída (`UserRequest`/`UserResponse`, `PostRequest`/`PostResponse`), evitando expor colunas internas (como o hash da senha) nas respostas da API.
- **Posts auto-relacionados**: um `Post` pode ter um `parent_id` apontando para outro post, permitindo modelar respostas/threads com uma única tabela, sem duplicar estrutura.
- **Configuração por ambiente com Dynaconf**: nenhuma credencial fica hardcoded no código — tudo é injetado via `default.toml` (valores padrão versionados), `settings.toml`/`.secrets.toml` (overrides locais, fora do versionamento) e variáveis de ambiente (usadas no `docker-compose.yaml` para configurar a conexão com o banco em cada ambiente).
- **Autenticação com access + refresh token**: o access token é de curta duração (30 min, configurável) e o refresh token permite renovação sem novo login (600 min, configurável), seguindo o padrão usado por APIs de produção.

---

## 🚀 Como rodar o projeto

Pré-requisitos: [Docker](https://www.docker.com/) e Docker Compose.

```bash
# Clonar o repositório
git clone <url-do-repositorio>
cd pamps

# Subir a API e o banco de dados
docker-compose up --build
```

A API estará disponível em `http://localhost:8000`, com documentação interativa (Swagger) em:

```
http://localhost:8000/docs
```

### Aplicando as migrações do banco

```bash
docker exec -it <nome-do-container-api> alembic upgrade head
```

### Criando um usuário

Via CLI (dentro do container):

```bash
docker exec -it <nome-do-container-api> pamps create-user seu@email.com seuusername suasenha
```

Ou gerando usuários fictícios para teste/demonstração:

```bash
docker exec -it <nome-do-container-api> pamps create-user-random --quantidade 10
```

### Outros comandos úteis da CLI

```bash
pamps user-list      # lista todos os usuários cadastrados
pamps shell           # abre um shell interativo (IPython) com os models já importados
pamps reset-db --force  # zera as tabelas do banco (útil em desenvolvimento/testes)
```

---

## 📚 Principais endpoints

| Método | Rota | Descrição | Autenticação |
|---|---|---|---|
| `POST` | `/token` | Login (retorna access + refresh token) | — |
| `POST` | `/refresh_token` | Renova o access token | — |
| `POST` | `/user/` | Cria um novo usuário | — |
| `GET` | `/user/` | Lista usuários | — |
| `GET` | `/user/{username}/` | Detalhes de um usuário | — |
| `POST` | `/post/` | Cria um post (ou uma resposta, via `parent_id`) | ✅ Bearer token |
| `GET` | `/post/` | Lista os posts principais (sem respostas) | — |
| `GET` | `/post/{post_id}/` | Detalhes de um post, incluindo suas respostas ordenadas por data | — |
| `GET` | `/post/user/{username}/` | Posts de um usuário (com filtro opcional `include_replies`) | — |

A lista completa e interativa (com exemplos de payload) está sempre disponível em `/docs`.

---

## 🗄️ Modelo de dados

```
User (1) ──< (N) Post
Post (1) ──< (N) Post   (auto-relacionamento: parent → replies)
```

- Um usuário pode ter vários posts.
- Um post pode ter várias respostas (outros posts apontando para ele via `parent_id`), permitindo montar threads de conversa — as respostas de um post vêm ordenadas cronologicamente.

---

## ✅ Testes automatizados

O projeto tem testes de integração (`pytest` + `httpx`/`TestClient` do FastAPI) cobrindo o fluxo real da API: autenticação, criação de posts, respostas encadeadas e as diferentes formas de listagem.

Os testes rodam contra um banco Postgres de teste isolado (`pamps_test`), separado do banco de desenvolvimento.

### Rodando a suíte de testes

Com o Docker instalado, o script abaixo sobe o ambiente, roda as migrações, executa os testes e derruba tudo em seguida:

```bash
bash test.sh
```

(no Windows, rode pelo Git Bash ou WSL — o PowerShell não interpreta scripts `.sh` nativamente)

Ou, manualmente, passo a passo:

```bash
PAMPS_DB=pamps_test docker-compose up -d
docker-compose exec api alembic upgrade head
docker-compose exec api pytest -v tests/
docker-compose down
```

---

## 🔧 Desenvolvimento local (sem Docker)

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1

pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .
```

O projeto usa **Python 3.10**, alinhado com a imagem base do Dockerfile, para evitar inconsistências entre ambiente local e produção.

Dependências travadas via [`pip-tools`](https://github.com/jazzband/pip-tools): o arquivo-fonte é o `requirements.in`, e o `requirements.txt` é gerado com `pip-compile`.

---

## 🛣️ Próximos passos

O core do projeto (autenticação, posts, respostas encadeadas e testes) está funcional e testado. Alguns pontos que ficaram fora do escopo desta versão, mapeados para uma próxima iteração:

- [ ] Paginação nas rotas de listagem
- [ ] Endpoints de atualização/remoção de posts e usuários
- [ ] CI/CD (lint + testes automatizados a cada push)
- [ ] Curtidas / interações entre usuários

---

## 👤 Autor

Desenvolvido por **Samuel** como projeto de estudo em desenvolvimento de APIs com FastAPI, com foco em arquitetura, boas práticas de configuração e containerização.
