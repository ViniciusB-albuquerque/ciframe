# Pesquisa — Sequências de Acordes Customizadas

## 1. Algoritmo de matching

Hoje a busca por sequência não calcula matching em tempo real. As 6 sequências estão hardcoded em `main.py:40-45`; a coluna `SEQ_FAMOSA` vira `musica.seqs_famosas` por `split(';')` em `main.py:63` e `musica.py:18`; e `/similares?sequencia=...` remove as vírgulas, procura a chave exata em `sequencias` e testa `str(id_seq) in musica.seqs_famosas` (`main.py:190-197`, `main.py:203-223`).

A regra que gerou a tag está em `scripts/generate_data_set.py:7-24`: lowercase (`linha 12`), a sequência precisa ser substring contígua da cifra inteira (`linha 13`) e todos os acordes da música precisam pertencer ao conjunto de acordes da sequência (`linhas 16-20`). Não há normalização de sufixos, enarmonias, inversões ou pontuação.

`musica.cifra` é a lista ordenada de acordes com repetições; `musica.acordes` é `list(set(cifra))`, sem ordem e sem duplicatas (`musica.py:16-17`). O carregamento do CSV está em `main.py:49-98`, e `main.py:50` descarta a primeira linha física; o arquivo atual não tem cabeçalho, então `data/top/dataset_final.csv:1` é uma música e não entra no catálogo.

## 2. Validação da hipótese

Reimplementei a regra de `get_famosas` sobre `musica.cifra`, ignorando maiúsculas, exigindo a sequência contígua e exigindo que todos os acordes da música pertençam ao conjunto da sequência. Rodei inline, sem criar arquivo, importando `main.py` (67.585 músicas carregadas) e comparei com `musica.seqs_famosas`:

| Sequência | matches | iguais à tag | falsos positivos | falsos negativos |
|---:|---:|---:|---:|---:|
| 0 | 199 | 67585 | 0 | 0 |
| 1 | 296 | 67585 | 0 | 0 |
| 2 | 4 | 67585 | 0 | 0 |
| 3 | 5 | 67585 | 0 | 0 |
| 4 | 7 | 67585 | 0 | 0 |
| 5 | 3 | 67585 | 0 | 0 |

A regra reimplementada reproduziu exatamente a tag nas 6 sequências, sem falsos positivos nem falsos negativos.

## 3. Banco de dados

O código atual não tem banco: o CSV é carregado em memória em `main.py:49-98`. O container é único e local (`Dockerfile:1-12`), sem `VOLUME`; gravações em disco vão para o layer gravável do container. Opções embarcadas sem serviço externo incluem SQLite (biblioteca padrão, arquivo único), TinyDB (JSON em Python puro) e `shelve`/`dbm` (chave-valor da biblioteca padrão). Os prós e contras estão em “Trade-offs identificados”.

## 4. Frontend existente

A rota `#/porsequencia` está em `static/assets/js/routes.js:17-21`. O template `static/templates/sequencia.html:1-63` mostra as sequências em `ng-repeat` (`linha 6`), o select de gênero (`linhas 24-30`) e os resultados (`linhas 40-58`). O controller `static/assets/js/controllers/sequencia.js:1-105` define 4 sequências hardcoded (`linhas 2-31`), monta a string de acordes separada por vírgula (`linhas 55-61`) e faz `GET` relativo para `similares?sequencia=...` (`linhas 72-77`). Se houver gênero selecionado, acrescenta `&generos=<gênero>` (`linhas 74-76`).

O gênero vem da constante `GENEROS` em `static/assets/js/app.js:6-58`, não do endpoint `/generos` (`main.py:158-160`). As 4 sequências do frontend correspondem às chaves `BmGDA` (ID 0), `CGAmF` (ID 1), `GmF` (ID 4) e `CC7FFm` (ID 5); as IDs 2 (`EmG`) e 3 (`CA7DmG7`) só existem no backend (`main.py:40-45`).

## Registro das descobertas

- **Execução inline da pergunta 2:** a regra original reimplementada sobre `musica.cifra` bateu 100% com a tag: 199, 296, 4, 5, 7 e 3 matches, com 0 falsos positivos e 0 falsos negativos para cada sequência (tabela acima).
- **App rodando no Docker:** as 6 sequências retornaram 199, 296, 4, 5, 7 e 3 músicas, igual ao CSV. Ao reiniciar o container, 4 das 6 voltaram em outra ordem com o mesmo conjunto; a regressão precisa comparar conjuntos, não a ordem.
- **App no navegador:** o select de gênero apareceu com `Regional` e as buscas saíram com `generos=Regional`, voltando vazias, embora o código inicialize `vm.meuGenero = ""` (`static/assets/js/controllers/sequencia.js:44`) e só acrescente o parâmetro quando ele não é vazio nem `null` (`linhas 74-76`).
- **DeepWiki (commit `fb9700`):** acertou a regra do `get_famosas`, mas afirmou que a ordem é estável e não percebeu o descarte da primeira linha em `main.py:50`. O endpoint de sequência não ordena os resultados (`main.py:203-223`) e a lista global de gêneros vem de um `set` (`main.py:92`).

## Trade-offs identificados

### Algoritmo

- **Regra original de `get_famosas` (lowercase + sequência contígua + todos os acordes da música dentro do conjunto da sequência).**
  - Prós: reproduziu exatamente as tags atuais no teste inline (0 falsos positivos/negativos); mantém a semântica das 6 sequências existentes.
  - Contras: exige a sequência completa contígua e nenhum acorde extra na música; não normaliza sufixos, enarmonias, inversões ou pontuação; depende da ordem de `musica.cifra`.
- **Só sequência contígua em `musica.cifra`, sem exigir que todos os acordes da música pertençam à sequência.**
  - Prós: aceita músicas com acordes adicionais; é uma noção mais direta de “a sequência aparece na música”.
  - Contras: tende a produzir mais matches que a tag atual para as 6 sequências; não preserva necessariamente o resultado de regressão exato; ignora a condição de conjunto.
- **Regra diferente para as 6 originais e para as novas.**
  - Prós: mantém as 6 com a tag/regra atual e permite outra regra para sequências cadastradas.
  - Contras: cria dois critérios de matching no mesmo catálogo; resultados deixam de ser diretamente comparáveis; aumenta o número de caminhos de teste.

### Banco embarcado

- **SQLite (biblioteca padrão, arquivo único).**
  - Prós: sem serviço externo; SQL, transações, índices e schema explícito; arquivo único no container.
  - Contras: exige schema/migração; escrita concorrente depende de configuração (ex.: WAL); o arquivo precisa de um caminho persistente.
- **TinyDB (JSON em Python puro).**
  - Prós: dependência leve; formato simples; schema flexível para o catálogo de sequências.
  - Contras: sem SQL/índices relacionais; reescreve o arquivo; concorrência e atomicidade mais limitadas.
- **`shelve`/`dbm` (chave-valor da biblioteca padrão).**
  - Prós: sem dependência externa; API simples de chave-valor.
  - Contras: consultas limitadas; concorrência e portabilidade dependem do backend `dbm`; menos adequado a listagens e validações mais elaboradas.

### Persistência no Docker

- **Layer gravável do container (sem `VOLUME`, como em `Dockerfile:1-12`).**
  - Prós: nenhum flag extra; mantém o `docker run -p 8080:8080 ciframe` documentado em `AGENTS.md:23-25`; sobrevive a `docker stop`/`docker start` do mesmo container.
  - Contras: some com `docker rm` ou com um novo `docker run`; não fica visível no host; não funciona como backup.
- **Volume nomeado.**
  - Prós: persiste entre containers recriados; gerenciado pelo Docker; pode ser reutilizado por outro container.
  - Contras: exige mudar o comando/documentação para incluir `-v`; precisa de inicialização e permissões do diretório; adiciona um objeto de infraestrutura ao deploy.
- **Bind mount de um diretório do host.**
  - Prós: arquivo visível e copiável no host; facilita inspeção e backup.
  - Contras: depende de caminho absoluto; permissões do host podem conflitar com o usuário do container; menos portátil entre máquinas.

### Frontend

- **Manter as 4 sequências hardcoded (`static/assets/js/controllers/sequencia.js:2-31`).**
  - Prós: preserva o comportamento atual; não depende de endpoint de catálogo; sem estados de carregamento/erro.
  - Contras: o catálogo do frontend continua diferente do backend; incluir uma sequência nova exige editar JavaScript.
- **Carregar o catálogo real do backend e renderizá-lo na página.**
  - Prós: o frontend passa a refletir o catálogo persistido; sequências novas aparecem sem alterar o JS.
  - Contras: exige endpoint/estado de carregamento e erro; altera o fluxo atual da página; exige ajustar a apresentação e os testes.
- **Híbrido: manter atalhos fixos para as 4 e listar também o catálogo dinâmico.**
  - Prós: mantém acesso rápido às sequências atuais e mostra as novas.
  - Contras: duas fontes de sequências; precisa definir ordenação/deduplicação; mais estados e casos de teste.
- **Select de gênero hardcoded (`GENEROS` em `static/assets/js/app.js:6-58`) versus carregar de `/generos` (`main.py:158-160`).**
  - Prós do hardcoded: funciona sem requisição extra. Contras: pode divergir do backend (o frontend tem 51 entradas; o backend tem 52, incluindo `R&B;`).
  - Prós do endpoint: reflete os gêneros realmente carregados do CSV. Contras: adiciona uma requisição e estados de carregamento/erro ao select.
