# Plano — Sequências de Acordes Customizadas

## Contexto e decisões

- Antes da implementação, as 6 sequências eram hardcoded em `main.py:40-45` e a busca usava a tag `SEQ_FAMOSA`; o frontend tinha 4 sequências hardcoded em `static/assets/js/controllers/sequencia.js:2-31`. Não havia escrita nem banco.
- Decisão: SQLite da stdlib em `data/sequencias.db`, sem volume; seed das 6; regra única validada com 0 falsos positivos/negativos; `/similares` mantém o mesmo contrato.
- Fora de escopo: volume, autenticação/moderação, migrar músicas/gêneros para o banco e normalização de acordes. Execução sem prazo definido, na ordem abaixo; se a implementação divergir, atualizar este plano antes de seguir.

## Passos

1. [x] Adicionar `*.db` a `.gitignore` e `.dockerignore` para não versionar nem assar `data/sequencias.db` na imagem (`Dockerfile:8`).
2. [x] Criar `sequencias_db.py` com `sqlite3`: schema `sequencias(id, nome, acordes, chave UNIQUE, criado_em)`, `init_db(caminho)`, `listar_sequencias()`, `buscar_por_chave()`, `criar_sequencia()` e seed das 6 originais com `INSERT OR IGNORE`.
3. [x] Ler o caminho de `SEQUENCIAS_DB` (default `data/sequencias.db`), criar o diretório e inicializar/semear no import de `main.py`; abrir conexão por chamada, sem conexão global.
4. [x] Implementar `sequencia_aparece(acordes_seq, cifra)`: lowercase nos dois lados, sequência como subsequência contígua de `musica.cifra` e todos os acordes da música no conjunto da sequência (`scripts/generate_data_set.py:7-24`).
5. [x] Implementar `GET /sequencias` (lista `json.dumps` com `id`, `nome`, `acordes`, `chave`, `criado_em`) e `POST /sequencias`: aceitar `acordes` como lista ou string, normalizar para lowercase, rejeitar vazio com 400, duplicata devolve a existente com 200 e nova retorna 201.
6. [x] Alterar `/similares`: buscar a `chave` no SQLite e usar `sequencia_aparece` sobre `musica.cifra` no lugar de `str(id_seq) in musica.seqs_famosas` (`main.py:190-223`), preservando filtro de gênero, paginação de 100, `json.dumps` e `[]` para chave desconhecida.
7. [x] Atualizar `sequencia.js`: carregar `GET /sequencias` no init, adaptar `acordes` para `{acorde, cor}`, remover as 4 hardcoded, expor `cadastrarSequencia` via `POST` e recarregar o catálogo; manter a busca e enviar `generos` só quando selecionado (`linhas 72-77`).
8. [x] Atualizar `static/templates/sequencia.html`: renderizar o catálogo dinâmico, adicionar formulário de nome/acordes e estados de carregamento/erro do cadastro.
9. [x] Criar `tests/__init__.py` (pacote necessário para o discovery) e `tests/test_sequencias.py` com `unittest` + `app.test_client()`, sem dependência nova; definir `SEQUENCIAS_DB` para um `tempfile.TemporaryDirectory()` antes de importar `main`, para nunca tocar `data/sequencias.db`.
10. [x] Cobrir catálogo seedado, cadastro (201), duplicata (200, mesmo `id`, sem linha nova), validação vazia (400), busca de sequência nova e busca das 6 originais.
11. [x] Regressão: para cada uma das 6, paginar `/similares?sequencia=...` até página vazia e comparar o conjunto de `id_unico_musica` com o conjunto de `main.musicas` cuja tag `seqs_famosas` contém o ID legado; comparar conjuntos, não ordem (`01-research.md:39`).
12. [x] Rodar `python -m unittest discover -s tests -t . -v` e registrar cobertura e resultado em `04-test-report.md`.

## Arquivos afetados

| Arquivo | Mudança |
|---|---|
| `sequencias_db.py` (novo) | Conexão SQLite, schema, seed e operações do catálogo. |
| `main.py` | Init/seed, `GET`/`POST /sequencias`, lookup no banco e matching sobre `musica.cifra`. |
| `tests/__init__.py` (novo) | Marcador de pacote para `unittest discover -s tests -t .`. |
| `tests/test_sequencias.py` (novo) | API, cadastro/duplicata/validação, busca nova e regressão das 6. |
| `.gitignore`, `.dockerignore` | Ignorar `*.db`. |
| `static/assets/js/controllers/sequencia.js` | Catálogo dinâmico, cadastro e gênero opcional. |
| `static/templates/sequencia.html` | Lista dinâmica e formulário de cadastro. |
| `docs/features/sequencias-customizadas/04-test-report.md` | Cobertura, resultado da regressão e como rodar. |

## Riscos e mitigação

- Teste tocar o banco real se `SEQUENCIAS_DB` não for definido antes do import: helper de teste exige caminho em `TemporaryDirectory` e a suíte usa apenas ele.
- Paginação de 100 esconder matches das sequências com 199 e 296 músicas: paginar até página vazia antes de comparar.
- API devolver `acordes` como string `;` e o template esperar `{acorde, cor}`: adapter explícito no controller, validado por `temAcorde` e render.
- Ordem dos resultados mudar após restart (`01-research.md:39`): comparar por `id_unico_musica`, nunca por posição.
- `docker rm`/rebuild apagar `data/sequencias.db`: aceito no `0002-persist-custom-sequences.md`; volume fora de escopo, registrar no relatório.
- POST concorrente da mesma sequência: `chave UNIQUE` + `INSERT OR IGNORE`; ao detectar existente, devolver a linha já gravada.

## Definição de pronto

- `GET /sequencias` lista as 6 seedadas e não duplica o seed em reimport.
- Cadastro novo retorna 201 e aparece no `GET`; duplicata retorna 200 com o mesmo `id`; entrada vazia retorna 400.
- Busca por sequência cadastrada aplica a regra sobre `musica.cifra` e retorna as músicas esperadas.
- As 6 originais retornam, em todas as páginas, conjunto de `id_unico_musica` idêntico ao conjunto marcado por `seqs_famosas`.
- `#/porsequencia` lista o catálogo da API, cadastra e busca; `generos` só vai na busca quando escolhido.
- `*.db` ignorado, nenhuma dependência nova e respostas continuam com `json.dumps`.
- `python -m unittest discover -s tests -t . -v` passa.
