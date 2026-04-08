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

### Schritt C: Das Etikett gestalten (Reiter „Etikett“)
Hier zeichnest du dein Layout:
1. Wähle ein Werkzeug (z.B. **BC** für Barcode oder **T** für Text).
2. Klicke auf das weiße Etikett, um das Objekt zu platzieren.
3. Klicke ein Objekt doppelt an, um die **Eigenschaften** zu öffnen.
4. **Platzhalter nutzen:** Um Daten aus deiner Tabelle zu drucken, schreibe den Feldnamen in eckigen Klammern: `[~Feldname~]`. Beispiel: `[~Barcode~]`.

### Schritt D: Vorschau und Export (Reiter „Druck“)
1. Gehe in den Reiter **„Druck“**.
2. Klicke oben auf die Pfeile (◀ ▶), um durch deine Datensätze zu blättern.
3. Das Programm füllt die Platzhalter automatisch mit den echten Werten aus deiner Tabelle.
4. **Export:** Speichere das Ergebnis als **PDF** oder **PNG**.
5. **Archivierung:** Mit **„In DB speichern“** wird das Etikett dauerhaft als Bild in der Datenbank archiviert (erscheint in der Liste rechts).

---

## 🛠️ 3. Fehlersuche & Tipps

*   **Barcode wird nicht angezeigt:** Überprüfe, ob deine Daten für den gewählten Typ gültig sind (z.B. braucht ein EAN-13 genau 13 Ziffern).
*   **Platzhalter leer:** Prüfe im Reiter „Daten -> Felder bearbeiten“, ob der Feldname exakt mit deinem Platzhalter übereinstimmt (z.B. `[~ArtNr~]`). Die Groß-/Kleinschreibung wird vom Programm automatisch toleriert.
*   **Keine DLL nötig:** Dieses Programm nutzt eine integrierte Python-Engine für Barcodes. Es muss keine zusätzliche `zint.dll` mehr installiert werden.

---
*Version 1.1 / April 2026*
