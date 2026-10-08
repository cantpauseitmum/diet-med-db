# Diet-Med DB (`diet-med-DB`)

Kontener bazy danych PostgreSQL 16 dla projektu **Diet-Med**, zoptymalizowany do uruchamiania w stacku **Portainer** oraz jako samodzielny kontener.

## Zawartość repozytorium
- `init-scripts/01_init_schema.sql` – definicja tabel:
  - `dolegliwosci`: kolumny `id` (PK), `kod` (NOT NULL UNIQUE)
  - `insulinoopornosc_produkty`: kolumny `id` (PK), `rodzaj` (NOT NULL UNIQUE), `status` (NOT NULL CHECK 'zalecane', 'dozwolone', 'ograniczone', 'zakazane'), `ilosc`, `jednostka`, `komentarz`
  - `niedoczynnosc_tarczycy_produkty`: kolumny `id` (PK), `rodzaj` (NOT NULL UNIQUE), `status` (NOT NULL CHECK 'zalecane', 'dozwolone', 'ograniczone', 'zakazane'), `ilosc`, `jednostka`, `komentarz`
  - `zgloszenia`: rejestracja zgłoszeń pacjentów z formularza TDP
- `init-scripts/02_seed_tdp.sql` – 12 dolegliwości z TDP
- `init-scripts/03_seed_insulinoopornosc.sql` – baza 384 unikalnych produktów Insulinooporność
- `init-scripts/04_seed_niedoczynnosc_tarczycy.sql` – baza 384 unikalnych produktów Niedoczynność tarczycy
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
