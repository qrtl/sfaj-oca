This module extends the Account Payment Terms functionality 
by introducing a cutoff date (cutoff_date) field in account.payment.term.line.
With this feature, user can define a specific cutoff date for payment terms. 
If an invoice is dated after this cutoff date, 
the system will automatically shift the due date by one additional month.
