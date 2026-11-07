# Relatório de testes — Sequências de Acordes Customizadas

## Cobertura

- `tests/test_sequencias.py` usa `unittest` e `app.test_client()`; o banco aponta para um `tempfile.TemporaryDirectory()` via `SEQUENCIAS_DB`, sem tocar `data/sequencias.db`.
- Catálogo: `GET /sequencias` devolve as 6 originais na ordem do seed, ainda com `json.dumps` (`Content-Type: text/html`); rodar o seed de novo não duplica.
- Cadastro: `POST /sequencias` aceita string e lista, normaliza para lowercase e retorna 201; duplicata retorna 200 com o mesmo `id`; acordes vazios ou corpo inválido retornam 400.
- Busca: sequência nova em dataset de fixture controlado, comparação case-insensitive, filtro de gênero e chave desconhecida retornando `[]`.
- Frontend: sintaxe validada com `node --check`; não há teste automatizado de browser.

## Teste de regressão obrigatório

Para cada uma das 6 sequências, o teste pagina `/similares?sequencia=...` até uma página vazia e compara o conjunto de `id_unico_musica` com o conjunto de músicas cuja tag `seqs_famosas` contém o ID legado. A comparação é por conjunto, não por ordem.

| Sequência | Músicas | Igual à tag |
|---|---:|---|
| `Bm,G,D,A` | 199 | sim |
| `C,G,Am,F` | 296 | sim |
| `Em,G` | 4 | sim |
| `C,A7,Dm,G7` | 5 | sim |
| `Gm,F` | 7 | sim |
| `C,C7,F,Fm` | 3 | sim |

Resultado da suíte: **13 testes, OK**, no container com Python 3.9. A paginação da maior sequência também foi verificada (100 na página 1 e 99 na página 2).

## Como rodar

```
docker run --rm ciframe python -m unittest discover -s tests -t . -v
```

Assume a imagem `ciframe` já construída.

## O que ficou de fora

- Não houve teste de browser/e2e do catálogo, do formulário de cadastro e do envio opcional de `generos`; a validação foi só de sintaxe e do contrato da API.
- A revisão de código não foi feita em outro terminal. O fluxo com `docker rm` também não foi exercitado; a perda de `data/sequencias.db` ao remover/recriar o container continua apenas documentada na ADR 0002.
- O caso de gênero pré-selecionado observado no navegador (`Regional` com `vm.meuGenero` vazio) não foi reproduzido de forma determinística; o controller agora só envia `generos` depois de uma mudança explícita no select.
- Persistência real com `docker stop`/`start`: por decisão da ADR 0002, o SQLite fica no layer do container, então sobrevive a stop/start e é apagado com `docker rm` ou novo container.
- Concorrência de cadastros simultâneos, volume nomeado, autenticação/moderação e normalização de acordes continuam fora de escopo.
