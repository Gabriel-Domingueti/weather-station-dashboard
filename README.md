# Weather Station Dashboard — Monitoramento Agrometeorológico e Alerta Fitossanitário do Cafeeiro

Dashboard de monitoramento agrometeorológico e sistema de alerta fitossanitário para a cafeicultura do **Sul de Minas Gerais** (*Coffea arabica* L.), desenvolvido em **FastAPI** (Backend) e **React + TypeScript** (Frontend) seguindo **Arquitetura Limpa (Clean Architecture)** e **TDD (Test-Driven Development)**.

O sistema opera **sem banco de dados** (*serverless data pipeline*): as séries horárias e os resumos diários ficam armazenados em planilhas CSV versionadas no próprio repositório (`data/`), atualizadas automaticamente via **GitHub Actions** a partir de dados meteorológicos reais da reanálise **ECMWF/ERA5 + Open-Meteo** para os **10 principais polos cafeeiros do Sul de Minas** e integradas ao **ESP32 + BME280 / ThingSpeak**.

---

## Sumário

- [Visão Geral e Arquitetura](#visão-geral-e-arquitetura)
- [Municípios Monitorados (Sul de Minas)](#municípios-monitorados-sul-de-minas)
- [Fundamentação Científica e Modelos Matemáticos](#fundamentação-científica-e-modelos-matemáticos)
- [Estrutura do Repositório](#estrutura-do-repositório)
- [Endpoints da API REST](#endpoints-da-api-rest)
- [Como Executar Localmente](#como-executar-localmente)
- [Coleta e Atualização de Dados (ETL)](#coleta-e-atualização-de-dados-etl)
- [Testes Automatizados (TDD)](#testes-automatizados-tdd)
- [Configuração do GitHub Actions e Deploy](#configuração-do-github-actions-e-deploy)
- [Referências Bibliográficas](#referências-bibliográficas)

---

## Visão Geral e Arquitetura

```
  ECMWF / ERA5 & Open-Meteo (10 Polos Cafeeiros do Sul de Minas)
  ESP32 + Sensor BME280 --HTTPS--> ThingSpeak
                                       |
                                       v  (cron horário / diário)
                             GitHub Actions (ETL)
              scripts/fetch_sul_de_minas_weather.py & sync_data.py
                                       |
                                       v
                 data/raw/*.csv, data/aggregated/*.csv e
                 data/sul_de_minas/{cidade}.csv + {cidade}_daily.csv
                                       |
                                       v
         FastAPI Backend (Clean Architecture + Cache em Memória + APScheduler)
         Lê dados locais ou via raw.githubusercontent.com e expõe API REST
                                       |
                                       v
      React SPA (Medidores, Índices Agro, Alertas Simplificados, Gráficos)
```

### Principais Características Arquiteturais
- **Clean Architecture & TDD:** Separação estrita entre `domain` (modelos e equações agrometeorológicas puras), `application` (casos de uso e hooks), `infrastructure` (repositório CSV com limpeza automática e cache TTL, cliente ThingSpeak e cliente HTTP) e `api`/`ui` (rotas FastAPI e componentes React).
- **Sem Banco de Dados (CSV-first):** Ideal para reprodutibilidade científica e hospedagem gratuita permanente (sem risco de expiração de bancos gratuitos em nuvem).
- **Troca Dinâmica de Município:** Ao selecionar qualquer uma das 10 cidades do Sul de Minas no painel, **todos os componentes do dashboard** (medidores de temperatura/umidade/pressão, setas de tendência, escala barométrica calibrada pela altitude, GD Acumulado, DMF Diário, alertas fitossanitários, recordes mensais e gráfico histórico) são atualizados simultaneamente.
- **Linguagem Acessível ao Cafeicultor:** Os cálculos matemáticos complexos rodam no domínio do backend, enquanto o painel exibe diagnósticos diretos (`Risco Alto`, `Atenção`, `Risco Baixo`) e recomendações práticas de manejo no campo.

---

## Municípios Monitorados (Sul de Minas)

As coordenadas geográficas e altitudes barométricas seguem os polos estudados em Aparecido (2019), Pozza et al. (2021) e Silva et al. (2025):

| Município | Chave (`city`) | Latitude | Longitude | Altitude | Pressão Média |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Varginha** *(padrão)* | `varginha` | -21.5667 | -45.4061 | 940 m | ~911 hPa |
| **Três Pontas** | `tres_pontas` | -21.3683 | -45.5128 | 905 m | ~915 hPa |
| **Muzambinho** | `muzambinho` | -21.3464 | -46.5344 | 1033 m | ~901 hPa |
| **Boa Esperança** | `boa_esperanca` | -21.0664 | -45.5769 | 830 m | ~921 hPa |
| **Carmo de Minas** | `carmo_de_minas` | -22.1753 | -45.1508 | 1080 m | ~896 hPa |
| **Guaxupé** | `guaxupe` | -21.2869 | -46.6930 | 870 m | ~917 hPa |
| **Alfenas** | `alfenas` | -21.4137 | -45.9706 | 827 m | ~921 hPa |
| **Nova Resende** | `nova_resende` | -21.1043 | -46.4104 | 1184 m | ~885 hPa |
| **Carmo do Rio Claro** | `carmo_do_rio_claro` | -21.0046 | -46.0229 | 796 m | ~925 hPa |
| **Sto. Antônio do Amparo** | `santo_antonio_do_amparo` | -20.8899 | -44.8825 | 1145 m | ~889 hPa |

---

## Fundamentação Científica e Modelos Matemáticos

O módulo de domínio (`backend/app/domain/agrometeorology.py`) utiliza **exclusivamente modelos matemáticos empíricos e regressões agrometeorológicas validadas na literatura científica** (sem modelos de Machine Learning treinados com dados sintéticos, evitando viés):

### 1. Graus-Dia ($\text{GD}$) e Fenologia do Cafeeiro
Baseado em **Aparecido (2019, Cap. 3 — Eq. 7, Tab. 2 e Fig. 6)**, com temperatura basal inferior $T_b = 10,2\,^\circ\text{C}$ e início do ciclo fenológico em 1º de setembro:

$$\text{GD} = \max\left(0,\; \frac{T_{\max} + T_{\min}}{2} - 10,2\right)$$

### 2. Duração do Período de Molhamento Foliar ($\text{DMF}$ / $\text{LWD}$)
Baseado em **Sentelhas et al. (2008)**, utilizando o método do limiar de umidade relativa ($\text{UR} \ge 90\%$) para estimar o número de horas de folha molhada a partir de leituras horárias de umidade relativa.

### 3. Sistema de Alerta para 4 Doenças e Pragas do Cafeeiro
- **Ferrugem do Cafeeiro (*Hemileia vastatrix*):**
  - Regressão múltipla de incidência com variáveis defasadas de temperatura máxima/mínima e umidade relativa (**Aparecido, 2019 — Eq. 6, Tab. 4**) combinada ao índice de favorabilidade termohídrica ($18\text{–}26\,^\circ\text{C}$ e $\text{DMF} \ge 6\text{ h}$) e limiar de controle de 5% de incidência (**Pozza et al., 2021**).
- **Mancha-de-Phoma (*Phoma tarda*):**
  - Comprimento do tubo germinativo ($\text{CTG}$) e Área Abaixo da Curva de Progresso da Incidência ($\text{AACPI} / \text{AUDPC}$) em função da temperatura ($15\text{–}20\,^\circ\text{C}$) e do molhamento foliar (**Lorenzetti et al., 2015**), integrado aos sistemas de aviso de acumulado de horas com $\text{UR} \ge 90\%$ em 48h (**Silva et al., 2025**).
- **Cercosporiose / Olho-pardo (*Cercospora coffeicola*):**
  - Favorabilidade sob temperaturas elevadas ($> 25\,^\circ\text{C}$), alta insolação e déficit hídrico/umidade relativa reduzida.
- **Bicho-mineiro (*Leucoptera coffeella*):**
  - Favorabilidade em períodos quentes e secos ($\text{UR}_{\text{média}} < 65\%$, $\text{DMF} < 4\text{ h}$ e amplitude térmica diária $> 11\,^\circ\text{C}$).

---

## Estrutura do Repositório

```text
.
├── backend/
│   ├── app/
│   │   ├── api/routes.py                  # Endpoints REST FastAPI (com suporte a ?city=)
│   │   ├── application/use_cases.py       # Casos de uso (Latest, Summary, History, Records, Trend, Agro, Alerts)
│   │   ├── core/cache.py                  # Cache em memória e invalidação automática
│   │   ├── domain/
│   │   │   ├── agrometeorology.py         # Equações científicas (GD, DMF, Ferrugem, Phoma, Cercospora, Bicho-mineiro)
│   │   │   └── models.py                  # Entidades e contratos Pydantic
│   │   ├── infrastructure/
│   │   │   ├── csv_repository.py          # Leitura resiliente de CSVs locais/GitHub Raw com cache TTL por cidade
│   │   │   └── thingspeak_client.py       # Cliente HTTP para leitura em tempo real do ESP32/ThingSpeak
│   │   ├── config.py                      # Configurações via variáveis de ambiente
│   │   └── main.py                        # Inicialização FastAPI, CORS e APScheduler
│   └── tests/                             # Testes unitários e de integração do backend (Pytest / Unittest)
├── frontend/
│   └── src/
│       ├── domain/types.ts                # Tipos e interfaces TypeScript
│       ├── infra/api.ts                   # Cliente HTTP da API do backend
│       ├── application/hooks/             # React Query hooks (sincronizados por cidade selecionada)
│       └── ui/
│           ├── components/                # Medidores, Índices Agro, Alertas Fitossanitários, Recordes e Gráfico
│           └── pages/Dashboard.tsx        # Página principal com estado global de cidade, período e métrica
├── scripts/
│   ├── fetch_sul_de_minas_weather.py      # ETL de dados reais (ECMWF/ERA5 + Open-Meteo Forecast) para 10 cidades
│   └── sync_data.py                       # ETL incremental do canal ThingSpeak (ESP32)
├── data/
│   ├── raw/                               # Leituras horárias mensais (YYYY-MM.csv)
│   ├── aggregated/                        # daily_summary.csv e agrometeorological_indices.csv
│   └── sul_de_minas/                      # {cidade}.csv (horário) e {cidade}_daily.csv (diário + GD + DMF)
└── .github/workflows/
    ├── ci.yml                             # Pipeline de Testes (Backend Pytest + Frontend Build)
    └── sync-data.yml                      # Atualização automática diária/horária dos CSVs no repositório
```

---

## Endpoints da API REST

Todos os endpoints de leitura suportam o parâmetro opcional `?city=<chave_da_cidade>` (ex.: `?city=varginha`, `?city=alfenas`, `?city=muzambinho`):

| Método | Rota | Descrição |
| :---: | :--- | :--- |
| `GET` | `/api/health` | Verificação de saúde do serviço |
| `GET` | `/api/readings/latest?city=` | Última leitura horária (temperatura, umidade, pressão e status) |
| `GET` | `/api/readings/trend?city=` | Tendência das últimas 3h (`rising`, `falling`, `stable`) e alerta de chuva |
| `GET` | `/api/readings/daily-summary?city=` | Resumo diário (médias, mínimas e máximas) |
| `GET` | `/api/readings/agro-indices?city=` | Índices agrometeorológicos diários (`gd`, `gd_acumulado`, `dmf_hours`) |
| `GET` | `/api/readings/phytosanitary-alerts?city=` | Diagnóstico fitossanitário simplificado para as 4 doenças/pragas do café |
| `GET` | `/api/readings/monthly-records?city=` | Recordes de máxima e mínima do mês para a cidade selecionada |
| `GET` | `/api/readings/history?start=&end=&metric=&city=` | Série horária bruta para plotagem no gráfico (até 92 dias por consulta) |
| `POST` | `/api/refresh` | Invalida o cache em memória de todas as cidades (protegido por `X-Refresh-Token`) |

---

## Como Executar Localmente

### Opção 1: Com Docker Compose

```bash
cp .env.example backend/.env
docker compose up --build
```

- **Backend API:** `http://localhost:8000/api/health`
- **Frontend Web:** `http://localhost:5173`

### Opção 2: Sem Docker (Desenvolvimento)

```bash
# Terminal 1 — Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev
```

---

## Coleta e Atualização de Dados (ETL)

Para atualizar manualmente as planilhas de todas as 10 cidades do Sul de Minas até a data e hora de hoje com dados reais do ECMWF/ERA5 + Open-Meteo:

```bash
python3 scripts/fetch_sul_de_minas_weather.py --city varginha --start 2025-01-01 --all-cities --strict-real
```

- O script combina a série histórica consolidada (`archive-api.open-meteo.com`) com as leituras recentes em tempo real (`api.open-meteo.com/v1/forecast?past_days=5`), garantindo que **não haja lacuna de dias recentes**.
- Gera automaticamente:
  - `data/raw/YYYY-MM.csv`
  - `data/aggregated/daily_summary.csv`
  - `data/aggregated/agrometeorological_indices.csv`
  - `data/sul_de_minas/{cidade}.csv` e `data/sul_de_minas/{cidade}_daily.csv` para os 10 municípios.

---

## Testes Automatizados (TDD)

```bash
# Executar testes unitários de agrometeorologia e pipeline do Sul de Minas (stdlib/unittest)
PYTHONPATH=backend python3 -m unittest backend/tests/test_agrometeorology.py backend/tests/test_fetch_sul_de_minas.py -v

# Executar suíte completa do backend com Pytest
cd backend && pytest

# Executar testes de componentes do frontend com Vitest
cd frontend && npm test
```

---

## Configuração do GitHub Actions e Deploy

O workflow `.github/workflows/sync-data.yml` roda automaticamente de forma agendada (e também pode ser disparado manualmente na aba **Actions > Sync weather data > Run workflow**). Ele atualiza os CSVs de todas as 10 cidades do Sul de Minas, faz o commit automático na branch `main` e notifica o backend em produção (`POST /api/refresh`).

Em `Settings > Secrets and variables > Actions`, você pode configurar opcionalmente:

| Secret | Descrição |
| :--- | :--- |
| `THINGSPEAK_CHANNEL_ID` | ID do canal do ThingSpeak (para quando o ESP32 estiver em campo) |
| `THINGSPEAK_READ_API_KEY` | Read API Key do canal ThingSpeak (se privado) |
| `BACKEND_REFRESH_URL` | URL pública do backend no Render para invalidação imediata de cache |
| `BACKEND_REFRESH_TOKEN` | Token correspondente a `REFRESH_TOKEN` configurado no backend |

### Deploy em Produção (Render)
- **Backend:** Web Service Docker (`backend/Dockerfile`). Ao iniciar e a cada 30 minutos (ou via `/api/refresh`), sincroniza os CSVs atualizados do GitHub.
- **Frontend:** Static Site (`frontend/`), comando de build `npm run build`, diretório de publicação `dist`, apontando a variável `VITE_API_BASE_URL` para a URL do backend.

---

## Referências Bibliográficas

1. **APARECIDO, L. E. O.** *Sistema de alerta agrometeorológico para a previsão da ferrugem do cafeeiro (*Hemileia vastatrix*) no Sul de Minas Gerais*. Tese (Doutorado em Agronomia) — UNESP, Jaboticabal, 2019.
2. **LORENZETTI, E. R. et al.** Effect of temperature and leaf wetness on *Phoma tarda* and phoma leaf spot in coffee seedlings. *Coffee Science*, Lavras, v. 10, n. 1, p. 1–9, 2015.
3. **POZZA, E. A. et al.** Coffee Rust Forecast Systems in Minas Gerais, Brazil. *Agronomy*, v. 11, n. 7, 2021.
4. **SENTELHAS, P. C. et al.** Relative humidity as an estimator of leaf wetness duration. *Agricultural and Forest Meteorology*, v. 148, p. 392–400, 2008.
5. **SILVA, B. M. et al.** Warning systems for phoma leaf spot of coffee. *Acta Scientiarum. Agronomy*, v. 47, 2025.
