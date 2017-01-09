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
```
    ./pxar2POS.py --help
```

write FT at -20 parameters trimmed to 35 to default output folder:
```
    ./pxar2POS.py -m M2222
```

get parameters for module M2222 from first fulltest at -20, trimmed to 35:
```
    ./pxar2POS.py -m M2222 -T 35 -t m20_1 -o Parameters_m20_trim35/
```

get untrimmed parameters at +17:
```
    ./pxar2POS.py -m M2222 -T -1 -t p17 -o Parameters_p17_untrimmed/
```

interpolate DACs linearly between -20 and +17 ----> to +8 degrees and save in dedicated folder:
```
    ./pxar2POS.py -m M2222 -t p8 -o Parameters_p8/
```

get configuration from MySQL DB running at localhost
```
    ./pxar2POS.py -m M2222 -s http://127.0.0.1
```

create default configuration for a module which does not exist in DB
```
    ./pxar2POS.py -m M9999 -s default
```


### "--do" option

With this option, DACs/TBM parameters can be changed for the whole configuration at once. Pxar2POS always creates a new copy the the currently selected configuration (UserConfig.ini or -i switch) to a new one and only changed the new configuration.
Format is:
   {subfolder}:[{condition}?]{operator}:{key}:{value};...
with {subfolder} one of tbm/dac/..., {operator}: set/and/or/incr4bit/incr8bit. AND and OR instructions are computed bitwise. {key} specifies which line to change, e.g. which DAC, and {value} is the operand.
{condition} is an expression, which needs to be matched in the file before any single replacement (* is wildcard). It can be used to target only specific ROCs or layers.



### "--do" examples

increase Vdig on ROC 2 by 1 for all modules (take care of L1 naming convention here!!):
```
    ./pxar2POS.py --do "dac:*F_MOD*_ROC2?incr4bit:Vdd:1"
```


set the DisablePKAMCounter flags to 0 for L4 modules:
```
    ./pxar2POS.py --do "tbm:*_LYR4_*?set:TBMADisablePKAMCounter:0;tbm:*_LYR4_*?set:TBMBDisablePKAMCounter:0"
```


set token/header/trailer delay to 1 for all modules, without touching port delays:
```
    ./pxar2POS.py --do "tbm:or:TBMADelay:192;tbm:or:TBMBDelay:192"
```


set token/header/trailer delay to 0 for all modules, without touching port delays:
```
    ./pxar2POS.py --do "tbm:and:TBMADelay:63;tbm:and:TBMBDelay:63"
```
