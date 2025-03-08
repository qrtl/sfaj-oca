Go to *Settings > Technical > Reporting > Qweb Field Converter*, and create records
according to your needs.

For each record:

- Set **Model** and **Field** (required)
- Set **UoM** and **UoM Field**, or **Currency** and **Currency Field** only for fields
  of float type (optional)
- Set **Options** as a string representation of a dictionary (e.g., ``{"widget": "date"}``,
  ``{"widget": "monetary"}``, or ``{'widget': 'contact', 'fields': ['name', 'phone']}``)
- Set **Company** (optional)
- Set **Digits** (required only for float-type fields)
