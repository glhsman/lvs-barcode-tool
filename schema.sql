-- Drinkport-Barcode Python – MariaDB-Schema
-- Einmalig ausführen:  python db_setup.py
-- Voraussetzung: Datenbank 'drinkport_barcode' existiert bereits
-- Empfohlen: ALTER DATABASE drinkport_barcode CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ─── Projekte ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS projects (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    description TEXT,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    modified_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── Tabellenfelder (Spalten) pro Projekt ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS project_fields (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    project_id  INT NOT NULL,
    name        VARCHAR(100) NOT NULL,
    position    INT NOT NULL DEFAULT 0,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    INDEX idx_project (project_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── Datensätze ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS data_records (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    project_id  INT NOT NULL,
    selected    TINYINT(1) NOT NULL DEFAULT 1,
    position    INT NOT NULL DEFAULT 0,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    INDEX idx_project (project_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── Feldwerte pro Datensatz ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS record_values (
    record_id   INT NOT NULL,
    field_id    INT NOT NULL,
    value       TEXT,
    PRIMARY KEY (record_id, field_id),
    FOREIGN KEY (record_id) REFERENCES data_records(id) ON DELETE CASCADE,
    FOREIGN KEY (field_id)  REFERENCES project_fields(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── Etikettenformat pro Projekt ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS label_formats (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    project_id       INT NOT NULL UNIQUE,
    manufacturer     VARCHAR(100),
    product_name     VARCHAR(100),
    width_mm         FLOAT NOT NULL DEFAULT 100.0,
    height_mm        FLOAT NOT NULL DEFAULT 50.0,
    margin_top_mm    FLOAT NOT NULL DEFAULT 2.0,
    margin_bottom_mm FLOAT NOT NULL DEFAULT 2.0,
    margin_left_mm   FLOAT NOT NULL DEFAULT 2.0,
    margin_right_mm  FLOAT NOT NULL DEFAULT 2.0,
    `cols`           INT   NOT NULL DEFAULT 1,
    `rows`           INT   NOT NULL DEFAULT 1,
    col_gap_mm       FLOAT NOT NULL DEFAULT 0.0,
    row_gap_mm       FLOAT NOT NULL DEFAULT 0.0,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── Etikettenobjekte (Text, Barcode, Grafik, Formen) ─────────────────────────
CREATE TABLE IF NOT EXISTS label_objects (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    project_id  INT NOT NULL,
    type        ENUM('text','barcode','image','rect','ellipse','line') NOT NULL,
    x_mm        FLOAT NOT NULL DEFAULT 0.0,
    y_mm        FLOAT NOT NULL DEFAULT 0.0,
    width_mm    FLOAT NOT NULL DEFAULT 20.0,
    height_mm   FLOAT NOT NULL DEFAULT 10.0,
    rotation    FLOAT NOT NULL DEFAULT 0.0,
    z_order     INT   NOT NULL DEFAULT 0,
    properties  JSON,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    INDEX idx_project (project_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── Gespeicherte Etiketten (fertig gerendert) ────────────────────────────────
CREATE TABLE IF NOT EXISTS saved_labels (
    id           INT AUTO_INCREMENT PRIMARY KEY,
    project_id   INT NOT NULL,
    record_id    INT,
    name         VARCHAR(255),
    image_data   LONGBLOB NOT NULL,
    image_format VARCHAR(10) DEFAULT 'PNG',
    dpi          INT DEFAULT 300,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by   VARCHAR(100),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (record_id)  REFERENCES data_records(id) ON DELETE SET NULL,
    INDEX idx_project (project_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ─── Globale Etiketten-Vorlagen (nur Formate) ──────────────────────────────────
CREATE TABLE IF NOT EXISTS global_label_templates (
    id               INT AUTO_INCREMENT PRIMARY KEY,
    name             VARCHAR(255) NOT NULL,
    manufacturer     VARCHAR(100),
    product_name     VARCHAR(100),
    width_mm         FLOAT NOT NULL DEFAULT 100.0,
    height_mm        FLOAT NOT NULL DEFAULT 50.0,
    margin_top_mm    FLOAT NOT NULL DEFAULT 2.0,
    margin_bottom_mm FLOAT NOT NULL DEFAULT 2.0,
    margin_left_mm   FLOAT NOT NULL DEFAULT 2.0,
    margin_right_mm  FLOAT NOT NULL DEFAULT 2.0,
    `cols`           INT   NOT NULL DEFAULT 1,
    `rows`           INT   NOT NULL DEFAULT 1,
    col_gap_mm       FLOAT NOT NULL DEFAULT 0.0,
    row_gap_mm       FLOAT NOT NULL DEFAULT 0.0,
    UNIQUE INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;
