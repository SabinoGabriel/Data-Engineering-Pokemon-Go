# 🎮 Pokemon GO Black & White List Generator

Sistema automatizado para gerar listas de Pokémon baseadas em rankings PvP.

## 📋 Estrutura do Projeto

```
pokemon-go-lists/
├── config/
│   └── settings.yaml          # Configurações centralizadas
├── src/
│   ├── data_sources/          # Fontes de dados (APIs, scraping)
│   ├── processors/            # Processamento de dados
│   ├── core/                  # Lógica principal
│   ├── exporters/             # Exportadores (CSV, search strings)
│   └── utils/                 # Utilitários (logger, helpers)
├── scripts/
│   └── generate_lists.py      # Script principal
├── output/                    # Arquivos gerados
├── logs/                      # Logs da aplicação
├── cache/                     # Cache HTTP
└── requirements.txt           # Dependências
```

## 🚀 Setup Inicial

### 1. Criar ambiente virtual

```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar settings

Edite `config/settings.yaml` conforme necessário.

## 📦 Dependências Principais

- **requests**: HTTP client para APIs
- **requests-cache**: Cache de requisições HTTP
- **pyyaml**: Leitura de configurações
- **beautifulsoup4**: Web scraping
- **pandas**: Processamento de dados
- **colorlog**: Logs coloridos

## 🎯 Próximos Passos

- [ ] Implementar `pvpoke_client.py`
- [ ] Implementar `static_data.py`
- [ ] Implementar `pokeapi_client.py`
- [ ] Implementar `gohub_scraper.py`
- [ ] Implementar processors
- [ ] Implementar core logic
- [ ] Implementar exporters
- [ ] Criar script principal

## 📝 Status

✅ **FASE 1 - Setup Inicial**: Completo
- Estrutura de pastas criada
- requirements.txt configurado
- settings.yaml implementado
- Logger básico funcionando

🔄 **FASE 2 - Data Sources**: Aguardando implementação

## 🧪 Testar Logger

```bash
python src/utils/logger.py
```

## 📄 Licença

Projeto pessoal - Uso livre
