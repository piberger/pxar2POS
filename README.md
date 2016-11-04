# pxar2POS
converts pxar parameter files to POS files


### Requirements

- Python (2.7)
- MySQL-python ("pip install MySQL-python")
- ROOT (5.34+ or 6 recommended)


### Installation & running

- adjust configuration values in pxar2POS.py, e.g. path of module position table, which is a simple text file. It's format can bee seen in: ExampleData/modules.txt where as example 2 fictional modules M2222 and M2223 are entered.
- run ./pxar2POS.py -m M2222 to write the parameters for M2222 to the output folder defined in pxar2POS.py
- or load the pxar2POSConverter class directly from your application

Data is read from a remote MySQL server if config option DataSource contains 'http://' as prefix (see default), otherwise from local pxar folder structure.


### examples:
show all available command line options:
./pxar2POS.py --help

write FT at -20 parameters trimmed to 35 to default output folder:
./pxar2POS.py -m M2222

get parameters for module M2222 from first FT at -20, trimmed to 35:
./pxar2POS.py -m M2222 -T 35 -t m20_1 -o Parameters_m20_trim35/

get untrimmed parameters at +17:
./pxar2POS.py -m M2222 -T -1 -t p17 -o Parameters_p17_untrimmed/

interpolate DACs linearly between -20 and +17 ----> +8 degrees and save in dedicated folder:
./pxar2POS.py -m M2222 -t p8 -o Parameters_p8/

