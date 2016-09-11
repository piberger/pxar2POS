# pxar2POS
converts pxar parameter files to POS files

examples:

get parameters for module M2222 from first FT at -20, trimmed to 35:
./pxar2POS.py -m M2222 -T 35 -t m20_1 -o Parameters_m20_trim35/

get untrimmed parameters at +17:
./pxar2POS.py -m M2222 -T -1 -t p17 -o Parameters_p17_untrimmed/