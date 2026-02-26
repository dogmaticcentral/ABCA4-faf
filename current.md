Running

```bash
./faf28_workflows/cli.py run /media/ivana/portable/abca4/faf/all/Cherry_Coast/OD/CC_OD_10_5.tiff --start-from FafVasculature --stop-after FafROIHistogram
```
1. If FafInnerMask crashes, the execution proceeds to FafROIHistogram (is should not, get the whole stack of errors afterwards)