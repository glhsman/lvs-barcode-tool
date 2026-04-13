"""
Druck-Modul für Windows.
Verschickt PIL-Bilder direkt an einen Systemdrucker via GDI (Win32 API).
"""
import win32print
import win32ui
import win32con
from PIL import Image, ImageWin


def print_pil_image(pil_img: Image.Image, printer_name: str, title: str = "Barcode Forge Print"):
    """Druckt ein einzelnes PIL Image direkt."""
    print_pil_images([pil_img], printer_name, title)


def print_pil_images(pil_imgs: list[Image.Image], printer_name: str, title: str = "Barcode Forge Print"):
    """Druckt eine Liste von PIL Images in einem einzigen Druckauftrag."""
    import win32print
    import win32ui
    import win32con

    hDC = win32ui.CreateDC()
    hDC.CreatePrinterDC(printer_name)
    
    printable_area = hDC.GetDeviceCaps(win32con.HORZRES), hDC.GetDeviceCaps(win32con.VERTRES)
    
    hDC.StartDoc(title)
    
    for pil_img in pil_imgs:
        hDC.StartPage()
        dib = ImageWin.Dib(pil_img)
        dib.draw(hDC.GetHandleOutput(), (0, 0, printable_area[0], printable_area[1]))
        hDC.EndPage()

    hDC.EndDoc()
    hDC.DeleteDC()


def show_printer_properties(printer_name: str, parent_hwnd: int = 0):
    """Öffnet den nativen Windows-Einstellungsdialog (via rundll32)."""
    import subprocess
    
    try:
        # Dies öffnet das Fenster des Druckertreibers direkt über Windows-Mittel
        subprocess.Popen(['rundll32.exe', 'printui.dll,PrintUIEntry', '/p', '/n', printer_name])
    except Exception as e:
        print(f"Fehler beim Öffnen der Druckereigenschaften: {e}")


def list_printers() -> list[str]:
    """Liefert eine Liste aller installierten Drucker-Namen."""
    return [p[2] for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
