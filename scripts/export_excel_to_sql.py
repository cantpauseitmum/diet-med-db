#!/usr/bin/env python3
import glob
import os
import zipfile
import xml.etree.ElementTree as ET
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
CREATE TABLE IF NOT EXISTS sibo_produkty (
    id SERIAL PRIMARY KEY,
    rodzaj VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('dozwolone', 'umiarkowane', 'zakazane')),
    ilosc NUMERIC(10, 2) NULL,
    jednostka VARCHAR(50) NULL,
    komentarz TEXT NULL
);

-- Indeksy ułatwiające wyszukiwanie
CREATE INDEX IF NOT EXISTS idx_sibo_rodzaj ON sibo_produkty(rodzaj);
CREATE INDEX IF NOT EXISTS idx_sibo_status ON sibo_produkty(status);

-- 3. Tabela zgłoszeń z formularza pacjentów
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
    # Lista 12 dolegliwości z pliku TDP.odt
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

def generate_sibo_sql(excel_path, output_path):
    wb = openpyxl.load_workbook(excel_path)
    ws = wb["tabela baza csv"]
    
    rows = []
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
        
        if not status:
            continue
        
        qty = vals[4]
        try:
            qty_val = float(qty) if qty is not None else "NULL"
        except ValueError:
            qty_val = "NULL"
            
        unit = str(vals[5]).strip().replace("'", "''") if vals[5] else None
        comment = str(vals[6]).strip().replace("'", "''") if vals[6] else None
        
        name_escaped = name.replace("'", "''")
        unit_str = f"'{unit}'" if unit else "NULL"
        comment_str = f"'{comment}'" if comment else "NULL"
        
        rows.append(f"('{name_escaped}', '{status}', {qty_val}, {unit_str}, {comment_str})")
        
    lines = [
        "-- =========================================================",
        "-- Wypełnienie tabeli produktów SIBO (303 wiersze)",
        "-- =========================================================",
        "INSERT INTO sibo_produkty (rodzaj, status, ilosc, jednostka, komentarz) VALUES"
    ]
    lines.append(",\n".join(rows) + ";")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Generated {output_path} with {len(rows)} products")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    root_dir = os.path.dirname(base_dir)
    
    excel_candidates = glob.glob(os.path.join(root_dir, "*SIBO.xlsx"))
    excel_path = [f for f in excel_candidates if not f.endswith(".bak")][0]
    
    init_dir = os.path.join(base_dir, "init-scripts")
    os.makedirs(init_dir, exist_ok=True)
    
    generate_schema_sql(os.path.join(init_dir, "01_init_schema.sql"))
    generate_tdp_sql(os.path.join(init_dir, "02_seed_tdp.sql"))
    generate_sibo_sql(excel_path, os.path.join(init_dir, "03_seed_sibo.sql"))
