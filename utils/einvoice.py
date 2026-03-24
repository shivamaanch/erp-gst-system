import json
from datetime import date

def build_einvoice_payload(bill, company, buyer) -> dict:
    return {
        "Version": "1.1",
        "TranDtls": {"TaxSch":"GST","SupTyp":"B2B","RegRev":"N","EcmGstin":None,"IgstOnIntra":"N"},
        "DocDtls": {
            "Typ":  "INV",
            "No":   bill.bill_no,
            "Dt":   bill.bill_date.strftime("%d/%m/%Y"),
        },
        "SellerDtls": {
            "Gstin": company.gstin or "",
            "LglNm": company.name,
            "Addr1": company.address or "",
            "Loc":   "City",
            "Pin":   160001,
            "Stcd":  company.state_code or "03",
        },
        "BuyerDtls": {
            "Gstin": buyer.gstin or "URP",
            "LglNm": buyer.name,
            "Pos":   buyer.state_code or "03",
            "Addr1": buyer.address or "",
            "Loc":   "City",
            "Pin":   160001,
            "Stcd":  buyer.state_code or "03",
        },
        "ValDtls": {
            "AssVal": float(bill.taxable_amount or 0),
            "CgstVal": float(bill.cgst or 0),
            "SgstVal": float(bill.sgst or 0),
            "IgstVal": float(bill.igst or 0),
            "TotInvVal": float(bill.total_amount or 0),
        },
    }
