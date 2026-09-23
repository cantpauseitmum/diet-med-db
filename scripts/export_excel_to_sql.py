#!/usr/bin/env python3
import glob
import os
import shutil
import openpyxl

def generate_schema_sql(output_path):
    sql = """-- =========================================================
-- Inicjalizacja schematu bazy danych Diet-Med (diet-med-DB)
-- =========================================================

-- 1. Tabela z listą dolegliwości (TDP)
CREATE TABLE IF NOT EXISTS dolegliwosci (
    id SERIAL PRIMARY KEY,
    kod VARCHAR(100) NOT NULL UNIQUE
);

-- 2. Tabela produktów dla SIBO
DROP TABLE IF EXISTS sibo_produkty CASCADE;
CREATE TABLE IF NOT EXISTS sibo_produkty (
    id SERIAL PRIMARY KEY,
    rodzaj VARCHAR(255) NOT NULL UNIQUE,
    status VARCHAR(20) NOT NULL CHECK (status IN ('dozwolone', 'umiarkowane', 'zakazane')),
    ilosc NUMERIC(10, 2) NULL,
    jednostka VARCHAR(50) NULL,
    komentarz TEXT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_sibo_rodzaj ON sibo_produkty(rodzaj);
CREATE INDEX IF NOT EXISTS idx_sibo_status ON sibo_produkty(status);

-- 3. Tabela produktów dla Hashimoto
DROP TABLE IF EXISTS hashimoto_produkty CASCADE;
CREATE TABLE IF NOT EXISTS hashimoto_produkty (
    id SERIAL PRIMARY KEY,
    rodzaj VARCHAR(255) NOT NULL UNIQUE,
    status VARCHAR(20) NOT NULL CHECK (status IN ('dozwolone', 'umiarkowane', 'zakazane')),
    ilosc NUMERIC(10, 2) NULL,
    jednostka VARCHAR(50) NULL,
    komentarz TEXT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_hashimoto_rodzaj ON hashimoto_produkty(rodzaj);
CREATE INDEX IF NOT EXISTS idx_hashimoto_status ON hashimoto_produkty(status);

-- 4. Tabela produktów dla Insulinooporności
DROP TABLE IF EXISTS insulinoopornosc_produkty CASCADE;
CREATE TABLE IF NOT EXISTS insulinoopornosc_produkty (
    id SERIAL PRIMARY KEY,
    rodzaj VARCHAR(255) NOT NULL UNIQUE,
    status VARCHAR(20) NOT NULL CHECK (status IN ('dozwolone', 'umiarkowane', 'zakazane')),
    ilosc NUMERIC(10, 2) NULL,
    jednostka VARCHAR(50) NULL,
    komentarz TEXT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_insulinoopornosc_rodzaj ON insulinoopornosc_produkty(rodzaj);
CREATE INDEX IF NOT EXISTS idx_insulinoopornosc_status ON insulinoopornosc_produkty(status);

-- 5. Tabela zgłoszeń z formularza pacjentów
CREATE TABLE IF NOT EXISTS zgloszenia (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NULL,
    dolegliwosci_ids INTEGER[] NOT NULL,
    pdf_path VARCHAR(255) NULL,
    status VARCHAR(50) DEFAULT 'wygenerowano',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(sql)
    print(f"Generated {output_path}")

def generate_tdp_sql(output_path):
    dolegliwosci_kody = [
        "hashimoto",
        "insulinooporność",
        "cukrzyca",
        "nietolerancja histaminy",
        "nadciśnienie tętnicze",
        "wysoki poziom cholesterolu",
        "wysoki poziom trójglicerydów",
        "lipoedema",
        "nadwaga/otyłość",
        "SIBO",
        "IMO",
        "niedoczynność tarczycy"
    ]
    
    lines = [
        "-- =========================================================",
        "-- Wypełnienie tabeli dolegliwości (TDP)",
        "-- =========================================================",
        "INSERT INTO dolegliwosci (kod) VALUES"
    ]
    vals = [f"('{kod}')" for kod in dolegliwosci_kody]
    lines.append(",\n".join(vals) + " ON CONFLICT (kod) DO NOTHING;")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Generated {output_path} with {len(dolegliwosci_kody)} items")

def generate_table_sql(excel_path, table_name, title_name, output_path):
    wb = openpyxl.load_workbook(excel_path)
    ws = wb.active
    
    STATUS_PRIORITY = {"dozwolone": 1, "umiarkowane": 2, "zakazane": 3}
    products = {}
    
    for r in range(3, ws.max_row + 1):
        vals = [ws.cell(r, c).value for c in range(1, 8)]
        name = str(vals[0]).strip() if vals[0] is not None else ""
        if not name:
            continue
            
        # Jeśli tylko kolumna 1 ma wartość, to nagłówek kategorii
        if not any(vals[1:]):
            continue
        
        status = None
        if vals[1] and str(vals[1]).strip().lower() == "x":
            status = "dozwolone"
        elif vals[2] and str(vals[2]).strip().lower() == "x":
            status = "umiarkowane"
        elif vals[3] and str(vals[3]).strip().lower() == "x":
            status = "zakazane"
        elif any(vals[4:7]):
            # Jeśli produkt ma ilość/jednostkę/komentarz bez 'x', to z definicji warunkowość -> umiarkowane
            status = "umiarkowane"
        
        if not status:
            continue
        
        qty = vals[4]
        try:
            qty_val = float(qty) if qty is not None else None
        except (ValueError, TypeError):
            qty_val = None
            
        unit = str(vals[5]).strip() if vals[5] else None
        comment = str(vals[6]).strip() if vals[6] else None
        
        key = name.lower()
        if key not in products:
            products[key] = {
                "rodzaj": name,
                "status": status,
                "ilosc": qty_val,
                "jednostka": unit,
                "komentarze": [comment] if comment else []
            }
        else:
            existing = products[key]
            existing_score = STATUS_PRIORITY.get(existing["status"], 0)
            new_score = STATUS_PRIORITY.get(status, 0)
            
            # Wyższy priorytet (zakazane > umiarkowane > dozwolone)
            if new_score > existing_score:
                existing["status"] = status
                existing["ilosc"] = qty_val
                existing["jednostka"] = unit
                if comment and comment not in existing["komentarze"]:
                    existing["komentarze"].append(comment)
            elif new_score == existing_score and status == "umiarkowane":
                if qty_val is not None and existing["ilosc"] is not None:
                    if qty_val < existing["ilosc"]:
                        existing["ilosc"] = qty_val
                        existing["jednostka"] = unit
                elif qty_val is not None and existing["ilosc"] is None:
                    existing["ilosc"] = qty_val
                    existing["jednostka"] = unit
                if comment and comment not in existing["komentarze"]:
                    existing["komentarze"].append(comment)
            elif new_score == existing_score and status == "dozwolone":
                if comment and comment not in existing["komentarze"]:
                    existing["komentarze"].append(comment)

    rows = []
    for item in products.values():
        name_escaped = item["rodzaj"].replace("'", "''")
        qty_str = str(item["ilosc"]) if item["ilosc"] is not None else "NULL"
        
        if item["jednostka"]:
            u_esc = item["jednostka"].replace("'", "''")
            unit_str = f"'{u_esc}'"
        else:
            unit_str = "NULL"
            
        if item["komentarze"]:
            c_combined = " / ".join(item["komentarze"]).replace("'", "''")
            comm_str = f"'{c_combined}'"
        else:
            comm_str = "NULL"
            
        rows.append(f"('{name_escaped}', '{item['status']}', {qty_str}, {unit_str}, {comm_str})")
        
    lines = [
        f"-- =========================================================",
        f"-- Wypełnienie tabeli produktów {title_name} ({len(rows)} unikalnych wierszy)",
        f"-- =========================================================",
        f"DROP TABLE IF EXISTS {table_name} CASCADE;",
        f"CREATE TABLE IF NOT EXISTS {table_name} (",
        f"    id SERIAL PRIMARY KEY,",
        f"    rodzaj VARCHAR(255) NOT NULL UNIQUE,",
        f"    status VARCHAR(20) NOT NULL CHECK (status IN ('dozwolone', 'umiarkowane', 'zakazane')),",
        f"    ilosc NUMERIC(10, 2) NULL,",
        f"    jednostka VARCHAR(50) NULL,",
        f"    komentarz TEXT NULL",
        f");",
        f"CREATE UNIQUE INDEX IF NOT EXISTS idx_{table_name}_rodzaj ON {table_name}(rodzaj);",
        f"CREATE INDEX IF NOT EXISTS idx_{table_name}_status ON {table_name}(status);",
        f"",
        f"INSERT INTO {table_name} (rodzaj, status, ilosc, jednostka, komentarz) VALUES"
    ]
    lines.append(",\n".join(rows) + ";")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Generated {output_path} with {len(rows)} unique products (0 duplicates)")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    root_dir = os.path.dirname(base_dir)
    
    sibo_candidates = [f for f in glob.glob(os.path.join(root_dir, "*SIBO*.xlsx")) if not f.endswith(".bak")]
    hashimoto_candidates = [f for f in glob.glob(os.path.join(root_dir, "*Hashimoto*.xlsx")) if not f.endswith(".bak")]
    io_candidates = [f for f in glob.glob(os.path.join(root_dir, "*insulino*.xlsx")) if not f.endswith(".bak")]
    
    init_dir = os.path.join(base_dir, "init-scripts")
    os.makedirs(init_dir, exist_ok=True)
    
    generate_schema_sql(os.path.join(init_dir, "01_init_schema.sql"))
    generate_tdp_sql(os.path.join(init_dir, "02_seed_tdp.sql"))
    
    if sibo_candidates:
        generate_table_sql(sibo_candidates[0], "sibo_produkty", "SIBO", os.path.join(init_dir, "03_seed_sibo.sql"))
        
    if hashimoto_candidates:
        generate_table_sql(hashimoto_candidates[0], "hashimoto_produkty", "Hashimoto", os.path.join(init_dir, "04_seed_hashimoto.sql"))

    if io_candidates:
        generate_table_sql(io_candidates[0], "insulinoopornosc_produkty", "Insulinooporność", os.path.join(init_dir, "05_seed_insulinoopornosc.sql"))

    # Kopiowanie do backend/app/seeds
    backend_seeds_dir = os.path.join(root_dir, "diet-med-backend", "app", "seeds")
    if os.path.exists(backend_seeds_dir):
        for f in glob.glob(os.path.join(init_dir, "*.sql")):
            shutil.copy2(f, backend_seeds_dir)
        print(f"Copied all seed scripts to {backend_seeds_dir}")
