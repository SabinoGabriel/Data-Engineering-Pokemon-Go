# Pokemon GO PvP Safe Trash

[Read in English](README.md)

Monorepo para um ETL de rankings PvP de Pokemon GO e uma aplicacao de Lixeira Segura dinamica.

O backend extrai rankings do PvPoke, modela familias de Pokemon GO em SQLite e expoe uma API FastAPI que calcula a string de transferencia sob demanda. O frontend e um app Next.js mobile-first com sliders de rank para Great League, Ultra League e Master League.

## Stack

- Backend: Python, pandas, requests, SQLite, FastAPI, Pydantic, pytest
- Frontend: Next.js, React, TypeScript
- CI: GitHub Actions

## Arquitetura

Este README raiz traz apenas a visao geral do monorepo. Os detalhes de arquitetura estao em ingles em:

- [Backend architecture](backend/README.md)
- [Frontend architecture](frontend/README.md)

```text
.
|-- backend/
|   |-- README.md                 # Notas de arquitetura do backend
|   |-- requirements.txt
|   |-- pytest.ini
|   |-- cache/                    # SQLite local, ignorado pelo git
|   |-- config/
|   |-- tests/
|   `-- src/
|       |-- constants.py          # URLs, cortes por liga, regioes, sufixo da string
|       |-- database.py           # Schema SQLite e persistencia
|       |-- etl.py                # Orquestracao Extract -> Transform -> Load
|       |-- transform.py          # Propagacao de ranks por familia e helpers
|       |-- api/main.py           # App FastAPI
|       `-- data_sources/
|           `-- pvpoke_client.py  # Cliente PvPoke
|-- frontend/
|   |-- README.md                 # Notas de arquitetura do frontend
|   |-- package.json
|   `-- app/
|       |-- page.tsx              # UI dinamica da Lixeira Segura
|       `-- globals.css
`-- .github/workflows/ci.yml
```

## Regra de Negocio: Isolamento Regional

Formas regionais e formas base sao familias PvP separadas. O backend propaga utilidade de rank com esta chave:

```text
family_id|regional_form
```

Por exemplo, `FAMILY_VULPIX|alola` e `FAMILY_VULPIX|base` sao independentes. Alolan Ninetales pode proteger Alolan Vulpix, mas nunca protege Vulpix de Kanto.

Essa regra fica em `backend/src/transform.py` e e coberta por testes unitarios.

## Modelo Dinamico de Rankings

A tabela SQLite `pokemon_dimension` armazena ranks exatos e anulaveis:

- `rank_gl`
- `rank_ul`
- `rank_ml`

Pokemon fora do corte de uma liga recebem `NULL` naquela coluna. A API recebe os cortes ativos do frontend e considera uma familia protegida quando qualquer rank ativo esta dentro do Top N selecionado.

## Backend API

Para detalhes de arquitetura e limites planejados de reutilizacao, veja [backend/README.md](backend/README.md).

A partir de `backend/`:

```powershell
python -m pip install -r requirements.txt
python -m src.etl
uvicorn src.api.main:app --reload
```

Endpoints:

- `GET /health`
- `POST /trash-string`

Request:

```json
{
  "gl_top": 50,
  "ul_top": null,
  "ml_top": 40,
  "lang": "en",
  "max_length": null
}
```

Response:

```json
{
  "ids": [1, 3, 7],
  "query_string": "1,3,7&!shiny&!lucky&!shadow&!purified&!legendary&!mythical&!costume&!4*&!3*&!@special",
  "chunks": ["1,3,7&!shiny&..."],
  "mixed": [{ "pokedex_id": 38, "nome": "Ninetales", "protected_forms": ["alola"], "trash_forms": ["base"] }],
  "mixed_strings": [{ "label": "Base/Kanto", "pokedex_ids": [38], "chunks": ["!alola&!galar&!hisui&!paldea&38&!shiny&..."] }]
}
```

Regras de seguranca:

- `ids` / `chunks` so contem numeros da Pokedex em que **nenhuma** forma e protegida. A busca por numero do jogo pega todas as formas, entao um numero como o 38 (Ninetales de Kanto inutil, de Alola util) fica fora da string principal e aparece em `mixed`.
- `mixed_strings` sao strings experimentais por regiao (ex.: `alola&26,52&...`). So funcionam se a busca por `alola`/`galar`/`hisui`/`paldea` tambem trouxer as formas regionais. Confira o resultado na tela antes de transferir.
- `lang` (`en` ou `pt`) escolhe os termos de busca. No jogo os termos so funcionam no idioma configurado. Os termos `pt` **nao foram verificados no jogo** (vieram de listas de terceiros).
- O sufixo de seguranca exclui brilhante, sortudo, sombroso, purificado, lendario, mitico, traje, favorito, fundo, dinamax e gigamax (alem de 4*, 3* e golpes especiais). **Um termo que o jogo nao reconhece e ignorado sem aviso**, entao um Pokemon protegido ainda apareceria na busca. Antes de confiar em um termo, busque-o sozinho (sem o `!`) e confira se a lista mostra seus Pokemon daquele tipo: `brilhante`, `sortudo`, `sombroso`, `purificado`, `lendário`, `mítico`, `traje`, `@especial`, `favorito`, `fundo`, `dinamax`, `gigamax`.
- `max_length` divide a saida em blocos independentes (cada um com o sufixo de seguranca completo), caso o jogo corte buscas longas. O limite real do jogo nao e documentado.

## Frontend

Para detalhes de arquitetura e limites planejados de componentes/hooks, veja [frontend/README.md](frontend/README.md).

A partir de `frontend/`:

```powershell
npm install
npm run dev
```

O frontend espera a API em `http://localhost:8000`. Para trocar:

```powershell
$env:NEXT_PUBLIC_API_BASE_URL="http://localhost:8000"
```

Abra:

```text
http://localhost:3000
```

## Testes

```powershell
cd backend
python -m pytest
```
