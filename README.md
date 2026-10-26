# Diet-Med DB (`diet-med-DB`)

Kontener bazy danych PostgreSQL 16 dla projektu **Diet-Med**, zoptymalizowany do uruchamiania w stacku **Portainer** oraz jako samodzielny kontener.

## Zawartość repozytorium
- `init-scripts/01_init_schema.sql` – definicja tabel bazowych:
  - `dolegliwosci`: kolumny `id` (PK), `kod` (NOT NULL UNIQUE)
  - `insulinoopornosc_produkty`: 384 unikalne produkty
  - `niedoczynnosc_tarczycy_produkty`: 384 unikalne produkty
  - `sibo_produkty`: 384 unikalne produkty
  - `hashimoto_produkty`: 384 unikalne produkty
  - `nietolerancja_histaminy_produkty`: 384 unikalne produkty
  - `lipoedema_produkty`: 384 unikalne produkty
  - `zgloszenia`: rejestracja zgłoszeń pacjentów z formularza TDP
- `init-scripts/02_seed_tdp.sql` – 12 dolegliwości z TDP
- `init-scripts/03_seed_insulinoopornosc.sql` – baza produktów Insulinooporność
- `init-scripts/04_seed_niedoczynnosc_tarczycy.sql` – baza produktów Niedoczynność tarczycy
- `init-scripts/05_seed_sibo.sql` – baza produktów SIBO
- `init-scripts/06_seed_hashimoto.sql` – baza produktów Hashimoto
- `init-scripts/07_seed_nietolerancja_histaminy.sql` – baza produktów Nietolerancja histaminy
- `init-scripts/08_seed_lipoedema.sql` – baza produktów Lipoedema
- `scripts/export_excel_to_sql.py` – skrypt do automatycznej detekcji i generacji plików SQL z aktualnych plików Excela
- `Dockerfile` – obraz oparty o `postgres:16-alpine`

## Uruchomienie lokalne (Docker)

```bash
docker build -t diet-med-db .
docker run -d \
  --name diet-med-DB \
  -p 5432:5432 \
  -e POSTGRES_DB=diet_med \
  -e POSTGRES_USER=diet_user \
  -e POSTGRES_PASSWORD=diet_password \
  diet-med-db
```

## Publikacja na GitHub (jako osobne repozytorium)

```bash
cd diet-med-db
git init
git add .
git commit -m "Initial commit: diet-med-db container with schema and SIBO/TDP seeds"
git branch -M main
git remote add origin git@github.com:TWOJ_USER/diet-med-db.git
git push -u origin main
```
