FROM postgres:16-alpine

LABEL maintainer="Diet-Med Team"
LABEL description="PostgreSQL database container for Diet-Med (diet-med-DB)"

# Kopiowanie skryptów inicjalizacyjnych do katalogu uruchomieniowego postgresa
COPY init-scripts/ /docker-entrypoint-initdb.d/

# Domyślny port PostgreSQL
EXPOSE 5432
