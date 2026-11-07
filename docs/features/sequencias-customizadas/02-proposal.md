# Proposta — Sequências de Acordes Customizadas

## Abordagem escolhida

Uma única regra de matching para as 6 originais e para as novas, com o catálogo de sequências em SQLite dentro do container e o `/similares` mantendo o mesmo contrato.

### Algoritmo de matching

Comparação por acordes, ignorando maiúsculas: normaliza `musica.cifra` e a sequência para lowercase, exige a sequência como subsequência **contígua** da cifra e exige que **todos** os acordes da música pertençam ao conjunto de acordes da sequência. É a regra de `scripts/generate_data_set.py:7-24` reimplementada sobre `musica.cifra` e validada com 0 falsos positivos/negativos nas 6 (`01-research.md:13-24`). Não há normalização de sufixos, enarmonias, inversões ou pontuação.

### Banco de dados

SQLite via `sqlite3` da biblioteca padrão, arquivo único em `data/sequencias.db` no layer gravável do container, **sem volume**. Só o catálogo de sequências vai para o banco; músicas e gêneros continuam vindo do CSV em memória (`main.py:49-98`). Persiste `docker stop`/`start`; some com `docker rm`/novo `run` — aceito, volume está fora de escopo. Adicionar `*.db` a `.gitignore`/`.dockerignore` para não assar banco local na imagem (`Dockerfile:8`).

### Esquema de dados (alto nível)

Tabela `sequencias`: `id` INTEGER PRIMARY KEY AUTOINCREMENT, `nome` TEXT, `acordes` TEXT (tokens em lowercase separados por `;`), `chave` TEXT UNIQUE (tokens sem separador), `criado_em` TEXT. Na inicialização, semear as 6 de `main.py:40-45` com `INSERT OR IGNORE`. Sem migrations nesta fase.

### API

- `GET /sequencias` → lista de `{id, nome, acordes, chave, criado_em}`, via `json.dumps`.
- `POST /sequencias` → corpo `{nome, acordes}` (`acordes` como lista ou string `Bm,G,D,A`); normaliza para lowercase, exige ao menos um acorde. Se a `chave` já existe, devolve a sequência existente (200); senão cria (201). Anônimo, sem login.
- `GET /similares` continua igual: mesmos parâmetros, prioridade (`main.py:185-197`), filtro de gênero, paginação de 100 e resposta `json.dumps`. Internamente, o ramo de sequência passa a buscar a `chave` no SQLite em vez do dicionário hardcoded, e o matching sobre `musica.cifra` substitui `str(id_seq) in musica.seqs_famosas` (`main.py:203-223`).

### Frontend

`#/porsequencia` carrega o catálogo de `GET /sequencias` e o renderiza, substituindo as 4 sequências hardcoded (`static/assets/js/controllers/sequencia.js:2-31`); adiciona formulário de cadastro que chama `POST /sequencias` e recarrega o catálogo. A busca usa o mesmo fluxo (`sequencia.js:55-61`, `72-77`). O parâmetro `generos` só é enviado quando o usuário escolhe um gênero — nunca vazio/null (`sequencia.js:74-76`); o comportamento observado com `Regional` (`01-research.md:40`) precisa ser reproduzido e corrigido no formulário.

## Alternativas consideradas e descartadas

**Proposta 2 — originais pela tag e novas por regra própria, com matches pré-calculados.** Descartada: cria dois critérios de matching, exige tabela extra de matches e invalidação quando o CSV muda, e aumenta o custo do cadastro sem necessidade — a regra única já reproduziu a tag exatamente (0 falsos positivos/negativos).

## Escopo explícito

**Dentro do escopo:**

- SQLite no container, sem volume; seed das 6 sequências originais.
- `GET`/`POST /sequencias`, duplicata devolve a existente; `/similares` inalterado no contrato e nos resultados das 6.
- Catálogo dinâmico e formulário de cadastro em `#/porsequencia`; `generos` apenas quando escolhido.

**Fora do escopo (e por quê):**

- Volume/moderação e autenticação: decisão explícita de manter o cadastro anônimo e a persistência no layer.
- Migrar músicas/gêneros para o banco: o CSV em memória continua sendo a fonte (`00-enunciado.md:60-62`).
- Normalização de acordes, ordenação estável e troca de `json.dumps` por `jsonify`: mudanças de comportamento não pedidas.
