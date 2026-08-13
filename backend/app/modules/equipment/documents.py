from io import BytesIO

import qrcode
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from app.modules.equipment.models import Equipment


def equipment_public_url(base_url: str, tracking_code: str) -> str:
    return f"{base_url.rstrip('/')}/equipment/{tracking_code}"


def generate_qr_png(content: str) -> bytes:
    qr = qrcode.QRCode(version=None, box_size=8, border=2)
    qr.add_data(content)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def generate_equipment_label(equipment: Equipment, base_url: str) -> bytes:
    output = BytesIO()
    page_width, page_height = 90 * mm, 50 * mm
    pdf = canvas.Canvas(output, pagesize=(page_width, page_height))
    pdf.setTitle(f"Etiqueta {equipment.tracking_code}")

    qr_bytes = generate_qr_png(equipment_public_url(base_url, equipment.tracking_code))
    pdf.drawImage(
        ImageReader(BytesIO(qr_bytes)),
        5 * mm,
        5 * mm,
        width=40 * mm,
        height=40 * mm,
        preserveAspectRatio=True,
        mask="auto",
    )

    text_x = 48 * mm
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(text_x, 40 * mm, equipment.tracking_code)
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(text_x, 33 * mm, f"{equipment.equipment_type.name[:24]}")
    pdf.setFont("Helvetica", 8)
    pdf.drawString(text_x, 28 * mm, f"{equipment.brand[:20]} {equipment.model[:20]}")
    pdf.drawString(text_x, 22 * mm, f"Patrimônio: {equipment.asset_number or 'N/A'}")
    pdf.drawString(text_x, 17 * mm, f"Série: {(equipment.serial_number or 'N/A')[:24]}")
    pdf.drawString(text_x, 11 * mm, f"Status: {equipment.current_status[:24]}")
    pdf.save()
    return output.getvalue()

