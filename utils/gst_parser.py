import json, openpyxl
from datetime import datetime

def parse_2b_json(file_obj) -> list:
    data    = json.load(file_obj)
    docdata = data.get("data",{}).get("docdata",{})
    records = []
    for supplier in docdata.get("b2b",[]):
        gstin = supplier.get("ctin","")
        name  = supplier.get("trdnm","")
        for inv in supplier.get("inv",[]):
            records.append({
                "supplier_gstin": gstin, "supplier_name": name,
                "invoice_no":     inv.get("inum",""),
                "invoice_date":   _parse_date(inv.get("dt","")),
                "invoice_type":   inv.get("typ","B2B"),
                "taxable_value":  float(inv.get("val",0)),
                "igst":           float(inv.get("igst",0)),
                "cgst":           float(inv.get("cgst",0)),
                "sgst":           float(inv.get("sgst",0)),
                "itc_available":  inv.get("itcavl","Y") == "Y",
            })
    return records

def parse_2b_excel(file_obj) -> list:
    wb = openpyxl.load_workbook(file_obj)
    ws = wb.active
    records = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[0]: continue
        records.append({
            "supplier_gstin": str(row[0] or ""),
            "supplier_name":  str(row[1] or ""),
            "invoice_no":     str(row[2] or ""),
            "invoice_date":   row[3] if isinstance(row[3], type(datetime.today().date())) else None,
            "taxable_value":  float(row[4] or 0),
            "cgst":           float(row[5] or 0),
            "sgst":           float(row[6] or 0),
            "igst":           float(row[7] or 0),
            "itc_available":  True,
        })
    return records

def _parse_date(s):
    try: return datetime.strptime(s, "%d-%m-%Y").date()
    except: return None
