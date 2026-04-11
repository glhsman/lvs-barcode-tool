# 📖 Handbuch: Drinkport-Barcode – Python Edition

Dieses Programm ist ein grafischer Etiketten-Editor mit direkter Datenbankanbindung. Es ermöglicht das Design von individuellen Etiketten, das Verwalten von Druckdaten und den Export als Bild oder PDF.

---

## ⚙️ 1. Die Datenbank-Architektur

Alle Daten werden permanent in einer MariaDB-Datenbank gespeichert. Dies ermöglicht den Zugriff von mehreren Arbeitsplätzen aus.

| Bereich | Datenbank-Tabelle | Funktion |
| :--- | :--- | :--- |
| **Projekte** | `projects` | Jedes Projekt (z.B. "Inventur", "Versand") hat eigene Felder und Layouts. |
| **Spalten** | `project_fields` | Definiert die Datenstruktur pro Projekt (z.B. "Art-Nr", "Preis"). |
| **Daten** | `data_records` | Speichert die einzelnen Zeilen (Datensätze) deiner Druckdaten. |
| **Werte** | `record_values` | Speichert die Inhalte pro Zelle für jeden Datensatz. |
| **Design** | `label_objects` | Speichert die Position, Größe und Art (Text, Barcode, Bild) der Objekte. |
| **Formate** | `label_formats` | Speichert die Etikettengröße (mm) und wie viele auf einen Bogen liegen. |
| **Bilder** | `saved_labels` | Speichert gerenderte Etiketten-Ergebnisse als PNG-Bilder (BLOB). |

---

## 🚀 2. Schritt-für-Schritt Workflow

### Schritt A: Projekt anlegen oder wählen
Wähle im Dropdown oben ein bestehendes Projekt oder klicke auf **„Neu“**, um einen neuen Namen zu vergeben. Jedes Projekt startet mit einem leeren Datenblatt und einem Standard-Etikett (100 x 50 mm).

### Schritt B: Die Datenstruktur definieren (Reiter „Daten“)
Bevor du Daten eingibst, musst du dem Programm sagen, was du speichern willst:
1. Gehe in den Reiter **„Daten“**.
2. Klicke auf **„Felder bearbeiten“**.
3. Füge Felder hinzu (z.B. `Barcode`, `Bezeichnung`, `Menge`).
4. **WICHTIG:** Du kannst danach auf **„Hinzufügen“** klicken, um manuell Werte einzutragen, oder eine CSV-Datei **importieren**.

### Schritt C: Das Etikett Format wählen (optional)
Im **Reiter „Etikett"** → **„Format"**-Dialog findest du vordefinierte **Label-Templates**:
- **Versandetikett 100×50 mm** – Standard-Kleinetiketten
- **A4 Zweckform 3659 (48,5×25,4 mm)** – A4-Bogen mit 4 Spalten × 11 Reihen (44 Etiketten)
- **A4 Zweckform 3474 (105×70 mm)** – A4-Bogen mit 2 Spalten × 4 Reihen (8 Etiketten)
- **A6 Etikett (105×148 mm)** – Großes Versandlabel
- **Vorlage LVS-Etikett (105×148 mm)** – Firmenvorlage für LVS-Etiketten

Wähle ein Template aus der Dropdown-Liste und klicke **„Übernehmen"**, um Größe und Layout automatisch zu setzen. Du kannst die Werte anschließend manuell anpassen.

> **Tipp:** Die Vorlagen werden zentral in der MariaDB-Datenbank verwaltet. Administratoren können neue Vorlagen erstellen oder bestehende ändern, die dann sofort für alle Benutzer verfügbar sind.

### Schritt D: Das Etikett gestalten (Reiter „Etikett")
Hier zeichnest du dein Layout:
1. Wähle ein Werkzeug (z.B. **BC** für Barcode oder **T** für Text).
2. Klicke auf das weiße Etikett, um das Objekt zu platzieren.
3. Klicke ein Objekt doppelt an, um die **Eigenschaften** zu öffnen.
4. **Platzhalter nutzen:** Um Daten aus deiner Tabelle zu drucken, schreibe den Feldnamen in eckigen Klammern: `[~Feldname~]`. Beispiel: `[~Barcode~]`.

**Profitipps im Editor:**
- **Cursor-Feedback:** Der Mauszeiger zeigt dir automatisch, was passiert (Verschiebe-Symbol ⬌, Resize-Pfeile ↔, Zeichnen +)
- **Hover-Highlights:** Griffe werden blau hervorgehoben, wenn du sie ansteuerst
- **2D-Barcodes quadratisch:** QR-Codes, DataMatrix und andere 2D-Codes bleiben immer quadratisch beim Resize
- **Zoom (Strg + Mausrad):** 275% Default-Zoom für komfortables Arbeiten; fein regulierbar in 25%-Schritten

### Schritt E: Vorschau und Export (Reiter „Druck")
1. Gehe in den Reiter **„Druck"**.
2. Klicke oben auf die Pfeile (◀ ▶), um durch deine Datensätze zu blättern.
3. Das Programm füllt die Platzhalter automatisch mit den echten Werten aus deiner Tabelle.
4. **Export:** Speichere das Ergebnis als **PDF** oder **PNG**.
5. **Druck:** Mit **„Drucken …"** direkt an dein Etikett-Druckgerät senden.
6. **Archivierung:** Mit **„In DB speichern"** wird das Etikett dauerhaft als Bild in der Datenbank archiviert (erscheint in der Liste rechts).

---

## 🔐 4. Administrator-Modus (Template-Management)

Für die Verwaltung der globalen Etikettenformate steht das separate Programm **Drinkport-Barcode Admin** zur Verfügung. Dieses Tool dient ausschließlich der Pflege der Vorlagendatenbank.

### Funktionen im Admin-Tool:
1. **Vorlagen wählen:** In der linken Liste werden alle gespeicherten Formate mit Name und Hersteller angezeigt. Mit einem Klick werden die Details geladen.
2. **Vorlagen bearbeiten:** Du kannst Abmessungen, Ränder und Bogenlayouts (Spalten/Reihen) direkt anpassen. 
3. **Änderungen speichern:** Speichert die Werte in der Datenbank. Wenn du den Namen änderst, wird die Vorlage automatisch umbenannt.
4. **Als neue Vorlage speichern:** Erstellt eine Kopie der aktuellen Einstellungen unter einem neuen Namen.
5. **Vorlage löschen:** Entfernt veraltete Formate unwiederbringlich aus der Datenbank.
6. **Felder leeren:** Setzt das Formular zurück, um ein völlig neues Format (z.B. für einen neuen Drucker) zu definieren.

---

## 🛠️ 5. Fehlersuche & Tipps

*   **Barcode wird nicht angezeigt:** Überprüfe, ob deine Daten für den gewählten Typ gültig sind (z.B. braucht ein EAN-13 genau 13 Ziffern).
*   **Platzhalter leer:** Prüfe im Reiter „Daten -> Felder bearbeiten“, ob der Feldname exakt mit deinem Platzhalter übereinstimmt (z.B. `[~ArtNr~]`). Die Groß-/Kleinschreibung wird vom Programm automatisch toleriert.
*   **Keine DLL nötig:** Dieses Programm nutzt eine integrierte Python-Engine für Barcodes.

---
*Version 1.6.0 / Mai 2026*
