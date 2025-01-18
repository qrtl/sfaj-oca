To configure this module, you must first properly set up your lead time profiles:

1. Go to *Inventory > Configuration > Settings*. Find the section Delivery Lead Time
   Settings, and update the weights of Source Address and Desitination Address according
   to your specific requirements.
   - Source Address: Allocated to Warehouse (Src)
   - Destination Address: Equaly distributed to Country (Dest), State (Dest), and
     Partner (Dest)
2. Navigate to *Inventory > Configuration > Lead Time Profiles*, and create records
   according to the reality of delivery logistics.

Examples of how most matched lead time profile is determined:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When there are lead time profile records like this, and you have an order to deliver
from Main WH to Cust A:

| Warehouse (Src) | Country (Dest) | State (Dest) | Partner (Dest) | Lead Time (Days) |
|-----------------|----------------|--------------|----------------|------------------|
|                 | Japan          | Tokyo        | Cust A         |              3.0 |
| Second WH       | Japan          | Tokyo        | Cust A         |              7.0 |
| Main WH         | Japan          | Tokyo        |                |              5.0 |


Case 1:

If the weights are configured to be like this:

- Source Address: 1.0
- Destination Address: 1.0

| Warehouse (Src) | Country (Dest) | State (Dest) | Partner (Dest) | Lead Time (Days) |
|-----------------|----------------|--------------|----------------|------------------|
|                 | Japan          | Tokyo        | Cust A         |              3.0 | --> 0.0 + 1.0/3 + 1.0/3 + 1.0/3 = 1.0
| Second WH       | Japan          | Tokyo        | Cust A         |              7.0 | --> -1.0 for the Source Address mismatch
| Main WH         | Japan          | Tokyo        |                |              5.0 | --> 1.0 + 1.0/3 + 1.0/3 + 0.0 = 1.66667

As a result, 5 days of the Delivery Lead Time will be proposed for the sales order.

Case 2:

If the weights are configured to be like this:

- Source Address: 1.0
- Destination Address: 4.0

| Warehouse (Src) | Country (Dest) | State (Dest) | Partner (Dest) | Lead Time (Days) |
|-----------------|----------------|--------------|----------------|------------------|
|                 | Japan          | Tokyo        | Cust A         |              3.0 | --> 0.0 + 4.0/3 + 4.0/3 + 4.0/3 = 4.0
| Second WH       | Japan          | Tokyo        | Cust A         |              7.0 | --> -1.0 for the Source Address mismatch
| Main WH         | Japan          | Tokyo        |                |              5.0 | --> 1.0 + 4.0/3 + 4.0/3 + 0.0 = 3.66667

As a result, 3 days of the Delivery Lead Time will be proposed for the sales order.
