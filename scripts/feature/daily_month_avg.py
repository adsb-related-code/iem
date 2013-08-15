# Compute mixing ratio climatology

import iemdb
from pyIEM import mesonet
import math, numpy
ASOS = iemdb.connect("asos", bypass=True)
acursor = ASOS.cursor()
acursor.execute("""SELECT valid, tmpf, dwpf 
from alldata where station = 'DSM' and dwpf > -50 and dwpf < 90 and tmpf > 50 
and extract(month from valid) = 7 and 
extract(minute from valid + '10 minutes'::interval) < 11""")

Tmix = numpy.zeros( (101,), 'f')
cnts = numpy.zeros( (101,), 'f')
maxD = numpy.zeros( (101,), 'f')
for row in acursor:
  dwpc = mesonet.f2c( row[2] )
  e  = 6.112 * math.exp( (17.67 * dwpc) / (dwpc + 243.5));
  mixr =  0.62197 * e / (1000.0 - e)
  h = mesonet.heatidx(row[1], mesonet.relh(row[1], row[2]))

  Tmix[ row[0].year - 1913] += mixr
  cnts[ row[0].year - 1913] += 1.0
  if row[2] > maxD[ row[0].year - 1913 ]:
    maxD[ row[0].year - 1913 ] = row[2]

import matplotlib.pyplot as plt
import matplotlib

fig = plt.figure(figsize=(9,7))
ax = fig.add_subplot(211)

ax.bar(numpy.arange(1913,2014)-0.4, Tmix / cnts * 1000.0, fc='g', ec='g')

ax.set_title("Des Moines [KDSM] July Humidity [1935-2013]")
ax.set_ylabel("Avg Mixing Ratio ($g/kg$)")
ax.set_xlim(1934,2014)
ax.grid(True)

ax2 = fig.add_subplot(212)
ax2.bar(numpy.arange(1913,2014)-0.4, maxD, fc='b', ec='b')
ax2.set_title("Maximum Dew Point ")
ax2.set_ylabel("Dew Point $^{\circ}\mathrm{F}$")
ax2.set_ylim(65,85)
ax2.set_xlim(1934,2014)
ax2.grid(True)

import iemplot
fig.savefig('test.ps')
iemplot.makefeature('test')
