# Data Engineering Pokemon GO PvP ETL Dashboard

[Read in English](README.md)

Projeto de engenharia de dados em Python com pipeline ETL e dashboard interativo em Streamlit para rankings PvP do Pokemon GO.

O pipeline extrai dados do PvPoke, transforma as informacoes com pandas, grava o resultado curado em SQLite e gera uma string segura de transferencia para Pokemon sem utilidade PvP detectada na familia evolutiva.

## Stack Tecnica

- Python
- pandas
- requests
- SQLite
- Streamlit
- pytest
- GitHub Actions

## O Que Este Projeto Demonstra

- Arquitetura de pipeline ETL com camadas claras de Extract, Transform e Load
- Integracao com APIs e arquivos JSON hospedados no GitHub
- Modelagem de dados para regras de negocio especificas
- Transformacoes analiticas com pandas
- Persistencia local reprodutivel com SQLite
- Desenvolvimento de dashboard com Streamlit
- Testes automatizados para regras criticas de transformacao
- Estrutura de repositorio adequada para vagas de dados e Python

## Fontes de Dados

- Great League: top 150 do PvPoke
- Ultra League: top 100 do PvPoke
- Master League: top 40 do PvPoke
- Dimensao Pokemon: `gamemaster.json` do PvPoke

O projeto usa o `gamemaster.json` do PvPoke como dimensao principal porque ele representa melhor o universo do Pokemon GO: formas, Pokemon lancados, IDs usados no PvPoke, sombras e metadados de familia.

## Arquitetura

```text
.
|-- app.py                         # Entrada do Streamlit
|-- requirements.txt               # Dependencias Python
|-- README.md                      # Documentacao em ingles
|-- README.pt-BR.md                # Documentacao em portugues do Brasil
|-- LICENSE                        # Licenca MIT
|-- cache/                         # SQLite local, ignorado pelo git
|-- tests/                         # Testes unitarios das regras de transformacao
|-- .github/workflows/ci.yml       # CI com GitHub Actions
|-- src/
|   |-- constants.py               # URLs, cortes das ligas, regioes e sufixo de transferencia
|   |-- dashboard.py               # UI Streamlit e filtros
|   |-- database.py                # Schema e persistencia SQLite
|   |-- etl.py                     # Orquestracao Extract -> Transform -> Load
|   |-- transform.py               # Regras de negocio, formas regionais e familias
|   |-- data_sources/
|   |   |-- pvpoke_client.py       # Cliente para rankings e gamemaster do PvPoke
|   |   `-- static_data.py         # Dados auxiliares legados
|   `-- utils/
|       `-- logger.py              # Logger do projeto
```

## Regra Critica: Formas Regionais

Pokemon com a mesma especie base, mas formas regionais diferentes, sao tratados como entidades independentes. Por exemplo, Alolan Ninetales nunca protege Kanto Ninetales, e Galarian Stunfisk nunca protege Stunfisk base.

O ETL propaga utilidade PvP pela chave:

```text
family_id|forma_regional
```

Isso significa que `FAMILY_VULPIX|alola` e `FAMILY_VULPIX|base` sao familias separadas no calculo.

Essa regra fica implementada em `src/transform.py` e coberta por testes unitarios.

## Saida do Dashboard

A tabela principal mostra:

- `Pokedex ID`
- `Nome`
- `Forma Regional`
- `Quantidade de Listas`

A secao **Lixeira Segura** lista IDs unicos de Pokemon com `quantidade_listas == 0` e adiciona o sufixo de seguranca do Pokemon GO:

```text
&!shiny&!lucky&!shadow&!purified&!legendary&!mythical&!costume&!4*&!3*&!@special
```

## Como Rodar

Crie e ative a venv:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

Instale as dependencias:

```powershell
python -m pip install -r requirements.txt
```

Inicie o dashboard:

```powershell
streamlit run app.py
```

Abra:

```text
http://localhost:8501
```

## Rodando Testes

```powershell
pytest
```

## Banco Local

O ETL grava os dados em:

```text
cache/pokemon_go_pvp.sqlite
```

Tabelas principais:

- `raw_rankings`: snapshots crus dos rankings do PvPoke
- `pokemon_dimension`: dimensao final com `quantidade_listas`
- `metadata`: metadados de atualizacao

## Palavras-Chave do Repositorio

Este projeto foi estruturado para destacar termos comuns em vagas de dados e analytics:

`python`, `pandas`, `streamlit`, `sqlite`, `etl`, `data-engineering`, `dashboard`, `api-integration`, `pokemon-go`, `pvpoke`, `pytest`, `github-actions`

## Licenca

MIT.
