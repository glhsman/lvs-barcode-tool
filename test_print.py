import win32print
import win32ui
import win32con
import win32gui

def test_print_dlg():
    print("Versuche win32ui.CreatePrintDialog...")
    try:
        pd = win32ui.CreatePrintDialog(win32con.PD_RETURNDC)
        res = pd.DoModal()
        print(f"Ergebnis DoModal: {res}")
        if res == win32con.IDOK:
            print("Erfolg! Drucker DC erhalten.")
    except Exception as e:
        print(f"Fehler bei win32ui: {e}")

    print("\nVersuche win32print.GetDefaultPrinter...")
    try:
        p = win32print.GetDefaultPrinter()
        print(f"Standarddrucker: {p}")
    except Exception as e:
        print(f"Fehler bei GetDefaultPrinter: {e}")

if __name__ == "__main__":
    test_print_dlg()
