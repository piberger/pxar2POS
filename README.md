# pxar2POS
converts pxar parameter files to POS files

### Installation & running

- adjust configuration values in pxar2POS.py, e.g. path of module position table, which is a simple text file. It's format can bee seen in: ExampleData/modules.txt where as example 2 fictional modules M2222 and M2223 are entered.
- run ./pxar2POS.py -m M2222 to write the parameters for M2222 to the output folder defined in pxar2POS.py
- or load the pxar2POSConverter class directly from your application

Data is read from a remote MySQL server if config option DataSource contains 'http://' as prefix (see default), otherwise from local pxar folder structure.
