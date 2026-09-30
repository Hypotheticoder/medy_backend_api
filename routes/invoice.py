import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from db import get_db
from models.b2b_purchase_order import B2BPurchaseOrder
from models.distributor import DistributorUser
from models.pharma_shop import PharmaShopUser

router = APIRouter(prefix="/api/v1/b2b/invoices", tags=["B2B GST Invoices"])

@router.get("/{po_id}/download")
def download_tax_invoice(po_id: str, db: Session = Depends(get_db)):
    """
    Generates and streams an Indian GST-compliant B2B Tax Invoice PDF.
    """
    po = db.query(B2BPurchaseOrder).filter(B2BPurchaseOrder.po_id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")

    distributor = db.query(DistributorUser).filter(DistributorUser.distributor_id == po.distributor_id).first()
    shop = db.query(PharmaShopUser).filter(PharmaShopUser.shop_id == po.shop_id).first()

    if not distributor or not shop:
        raise HTTPException(status_code=400, detail="Incomplete buyer or seller profile records.")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="TitleStyle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        alignment=1,
        textColor=colors.HexColor("#1A202C")
    )
    meta_style = ParagraphStyle(
        name="MetaStyle",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#2D3748")
    )

    story = []

    # 1. Invoice Header
    story.append(Paragraph("<b>TAX INVOICE</b>", title_style))
    story.append(Paragraph("<font size=9 color='#718096'>Original for Recipient (B2B Pharmaceutical Supply)</font>", ParagraphStyle(name="Sub", alignment=1)))
    story.append(Spacer(1, 15))

    # 2. Buyer & Seller Details (2-Column Table)
    seller_info = f"""
    <b>SOLD BY (Distributor):</b><br/>
    <b>{distributor.company_name}</b><br/>
    {distributor.address}<br/>
    <b>GSTIN:</b> {distributor.gstin_no}<br/>
    <b>PAN:</b> {distributor.pan_number}<br/>
    <b>DL No (20B/21B):</b> Available on record<br/>
    <b>Phone:</b> {distributor.phone}
    """

    buyer_info = f"""
    <b>BILLED TO (Retailer):</b><br/>
    <b>{shop.shop_name}</b><br/>
    {shop.address}<br/>
    <b>GSTIN:</b> {getattr(shop, 'gst_number', 'UNREGISTERED') or 'N/A'}<br/>
    <b>PAN:</b> {getattr(shop, 'pan_number', 'N/A') or 'N/A'}<br/>
    <b>DL No (20/21):</b> {getattr(shop, 'license_number', 'N/A')}<br/>
    <b>Phone:</b> {shop.phone}
    """

    parties_table = Table(
        [
            [Paragraph(seller_info, meta_style), Paragraph(buyer_info, meta_style)]
        ],
        colWidths=[270, 270]
    )
    parties_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFC")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E0")),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(parties_table)
    story.append(Spacer(1, 10))

    # 3. Invoice Meta
    invoice_meta = [
        [
            Paragraph(f"<b>Invoice / PO No:</b> {po.po_id}", meta_style),
            Paragraph(f"<b>Date:</b> {po.created_at.strftime('%d-%b-%Y') if po.created_at else 'N/A'}", meta_style),
            Paragraph(f"<b>Payment Terms:</b> {po.payment_terms.upper()}", meta_style),
            Paragraph(f"<b>Status:</b> {po.po_status.upper()}", meta_style)
        ]
    ]
    meta_table = Table(invoice_meta, colWidths=[135, 135, 135, 135])
    meta_table.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))

    # 4. Itemized Product Table
    table_data = [
        ["#", "Batch", "Qty (Box)", "PTR (₹)", "Taxable (₹)", "CGST (₹)", "SGST (₹)", "Total (₹)"]
    ]

    items = po.items if isinstance(po.items, list) else []
    for idx, item in enumerate(items, start=1):
        qty = item.get("qty_boxes", 0)
        ptr = item.get("ptr", 0.0)
        taxable = qty * ptr
        gst_pct = item.get("gst_percentage", 12.0)
        cgst = (taxable * (gst_pct / 2 / 100))
        sgst = (taxable * (gst_pct / 2 / 100))
        line_total = taxable + cgst + sgst

        table_data.append([
            str(idx),
            item.get("batch_number", "N/A"),
            str(qty),
            f"{ptr:.2f}",
            f"{taxable:.2f}",
            f"{cgst:.2f}",
            f"{sgst:.2f}",
            f"{line_total:.2f}"
        ])

    # Totals Row
    table_data.append(["", "", "", "TOTALS:", f"₹ {po.subtotal:.2f}", f"₹ {po.cgst_amount:.2f}", f"₹ {po.sgst_amount:.2f}", f"₹ {po.total_invoice_amount:.2f}"])

    items_table = Table(table_data, colWidths=[25, 80, 55, 60, 80, 75, 75, 90])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ALIGN', (3,1), (-1,-1), 'RIGHT'),
        ('GRID', (0,0), (-1,-2), 0.5, colors.HexColor("#E2E8F0")),
        ('LINEABOVE', (0,-1), (-1,-1), 1, colors.HexColor("#2D3748")),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 25))

    # 5. Statutory Declaration / Footer
    footer_text = """
    <b>Terms & Conditions:</b><br/>
    1. Goods once sold will not be taken back unless subject to pharmaceutical recall.<br/>
    2. Certified that all medicines specified in this invoice do not contravene Section 18 of the Drugs and Cosmetics Act, 1940.<br/>
    3. Input Tax Credit (ITC) is subject to timely GST outward filing (GSTR-1).
    """
    story.append(Paragraph(footer_text, ParagraphStyle(name="Footer", fontSize=7, leading=10, textColor=colors.HexColor("#718096"))))

    doc.build(story)
    buffer.seek(0)

    filename = f"Tax_Invoice_{po.po_id}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"}
    )
