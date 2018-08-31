See a renered version of [trial_analysis](https://nbviewer.jupyter.org/github/cudmore/pie/blob/master/analysis/trial_analysis.ipynb) with plots.

See a renered version of [timeStampAnalysis](https://nbviewer.jupyter.org/github/cudmore/pie/blob/master/analysis/timeStampAnalysis.ipynb) with plots.

## Analysis

Jupyter notebook to analyze trial .txt files.

 - **trial_analysis**. Comparing GPIO events using Python time library versus the pigpio(d) library. Conclude that the pigpio(d) library is very precise.
 - **timeStampAnalysis**. Analyzing GPIO frame times and their intervals using the PiCamera time-stamp. Conclude, GPIO arrival is more precise than you would think.
 
## Conclude

The Raspberry Pi GPIO and camera should be reliable for use on a scope acquiring 30 fps.

## Running

These Jupyter notebooks should be run on an analysis machine, they should not be run on the Raspberry Pi. This assumes the Raspberry Pi is running a file server and the trial files can be accessed remotely.

```
# On a remote machine, change into folder that is mount point of a PiE server
cd /Volumes/pi15/pie/analysis

# run jupyer notebook (will open a web browser)
jupyter notebook
```

