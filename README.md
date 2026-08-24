# Weather Station Dashboard

Dashboard de uma estação meteorológica (ESP32 + BME280), sem banco de dados:
os dados brutos ficam em CSV versionado no repositório, atualizados por um
ETL agendado no GitHub Actions, com o ThingSpeak servindo como buffer/leitura
ao vivo.

## Arquitetura

```
ESP32 + BME280 --HTTPS--> ThingSpeak --cron--> GitHub Actions (ETL)
                                                       |
                                                       v
                                              data/*.csv (no repo)
                                                       |
                                                       v
                                          FastAPI backend (lê do GitHub raw,
                                          cacheia em memória, expõe REST)
                                                       |
                                                       v
                                    React SPA (filtros, gráficos) <- Browser
```

- `ThingSpeak` só é consultado diretamente pelo backend para a leitura "ao
  vivo" (`/api/readings/latest`). O histórico vem sempre dos CSVs.
- O backend **não depende de disco persistente**: ele busca os CSVs via
  `raw.githubusercontent.com` e mantém um cache em memória, refrescado
  periodicamente e também sob demanda (`POST /api/refresh`, chamado pelo
  workflow de ETL após cada commit).

## Estrutura do repositório

```
backend/     API FastAPI (domain / application / infrastructure / api)
frontend/    SPA React + Vite + TypeScript
scripts/     ETL (sync_data.py) rodado pelo GitHub Actions
data/        CSVs versionados (raw/ e aggregated/)
.github/     workflows de sync de dados e CI
```

## Rodando localmente com Docker

```bash
cp .env.example backend/.env
# edite backend/.env com o ID/API key do seu canal do ThingSpeak

docker compose up --build
```

- Backend: http://localhost:8000/api/health
- Frontend: http://localhost:5173

## Rodando sem Docker (dev)

```bash
# backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# frontend (outro terminal)
cd frontend
npm install
npm run dev
```

## Configurando os secrets no GitHub

Em `Settings > Secrets and variables > Actions`, adicione:

| Secret                    | Descrição                                 |
| ------------------------- | ----------------------------------------- |
| `THINGSPEAK_CHANNEL_ID`   | ID do canal do ThingSpeak                 |
| `THINGSPEAK_READ_API_KEY` | Read API Key (se o canal for privado)     |
| `BACKEND_REFRESH_URL`     | URL do backend em produção (opcional)     |
| `BACKEND_REFRESH_TOKEN`   | Deve bater com `REFRESH_TOKEN` do backend |

## Deploy

- **Backend**: Render (free tier) — build a partir de `backend/Dockerfile`.
  Free tier hiberna após 15 min de inatividade; o primeiro request após
  acordar recarrega o cache automaticamente.
- **Frontend**: pode ir para Render Static Site, Vercel, Netlify ou GitHub
  Pages (buildando com `npm run build` e apontando `VITE_API_BASE_URL` para
  a URL pública do backend).
