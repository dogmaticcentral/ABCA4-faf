Running
```bash
./faf28_workflows/cli.py run /media/ivana/portable/abca4/faf/all/Cherry_Coast/OD/CC_OD_10_5.tiff --start-from FafRecalibration --stop-after FafOuterMask
```
should run subgraph. 
Problems:
1. FafVasculature apparently saves to `faf_analysiss` directory
2. "FafOuterMask crashed: the argument '--outer-mask' does not seem to be switch"

```bash
./faf28_workflows/cli.py run /media/ivana/portable/abca4/faf/all/Cherry_Coast/OD/CC_OD_10_5.tiff --start-from FafVasculature --stop-after FafROIHistogram
```
1. "FafInnerMask crashed: the argument '--outer-mask' does not seem to be switch"
2. After FafInnerMask crashes, the execution proceeds to FafROIHistogram (is should not, get the whole stack of errors afterwards)