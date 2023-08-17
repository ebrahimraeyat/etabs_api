### etabs_api

etabs_api is a package written with python to communicates with [CSI ETABS](https://www.csiamerica.com/products/etabs) (2018 and above versions) and [CSI SAFE](https://www.csiamerica.com/products/safe) Softwares.

## Installation
Stable Release:

`pip install etabs-api`

## Simple example

```python
import find_etabs
etabs, filename = find_etabs.find_etabs(run=False, backup=False)
if (
    etabs is None or
    filename is None
    ):
    print('Error Occurred')
else:
    etabs.lock_and_unlock_model()
    ex, exn, exp, ey, eyn, eyp = etabs.load_patterns.get_seismic_load_patterns()

# Read Tables
table_key = 'Load Combination Definitions'
df = etabs.database.read(table_key, to_dataframe=True)
# write Tables
etabs.database.write(table_key=table_key, data=df)
```

