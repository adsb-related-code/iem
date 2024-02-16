<?php 
require_once "../../config/settings.inc.php";
require_once "../../include/myview.php";
$t = new MyView();
$t->title = "Max CSV Services";

$t->content = <<<EOF

<h3>Max CSV Services</h3>

<p>These are special services emitting CSV in a form that Max seems to like.</p>

<div class="well">
<h4>AHPS Observations</h4>

<code>https://mesonet.agron.iastate.edu/request/maxcsv/ahpsobs_\$NWSLI.txt</code>

<p>Provides data from the HML source for AHPS sites.
<a href="maxcsv/ahpsobs_AESI4.txt">maxcsv/ahpsobs_AMEI4.txt Example</a></p>
</div>

<div class="well">
<h4>AHPS Forecast</h4>

<code>https://mesonet.agron.iastate.edu/request/maxcsv/ahpsfx_\$NWSLI.txt</code>

<p>Provides forecast data from the HML source for AHPS sites.
<a href="maxcsv/ahpsfx_DEWI4.txt">maxcsv/ahpsfx_DEWI4.txt Example</a></p>
</div>

<div class="well">
<h4>AHPS Obs + Forecast</h4>

<code>https://mesonet.agron.iastate.edu/request/maxcsv/ahps_\$NWSLI.txt</code>

<p>Provides obs + forecast data from the HML source for AHPS sites.
<a href="maxcsv/ahps_DEWI4.txt">maxcsv/ahps_DEWI4.txt Example</a></p>
</div>

<div class="well">
<h4>Iowa Soil Moisture Network Currents</h4>

<code>https://mesonet.agron.iastate.edu/request/maxcsv/isusm.txt</code>

<p>Provides <a href="/agclimate/">ISU Soil Moisture Network</a> data, which
includes four inch depth soil temperatures.  Data is at least valid within
the previous 30 minutes.
 <a href="maxcsv/isusm.txt">maxcsv/isusm.txt Example</a></p>
</div>


<div class="well">
<h4>Iowa Winter Road Conditions</h4>

<code>https://mesonet.agron.iastate.edu/request/maxcsv/iaroadcond.txt</code>

<p>Provides Iowa DOT Winter Road conditions as a single point used for further
interactivity/symbology.
<a href="maxcsv/iaroadcond.txt">maxcsv/iaroadcond.txt Example</a></p>
</div>

<div class="well">
<h4>Iowa RWIS data</h4>

<code>https://mesonet.agron.iastate.edu/request/maxcsv/iarwis.txt</code>

<p>Provides current Iowa RWIS observations.
<a href="maxcsv/iarwis.txt">maxcsv/iarwis.txt Example</a></p>
</div>

<div class="well">
<h4>Iowa Airport data for yesterday</h4>

<code>https://mesonet.agron.iastate.edu/request/maxcsv/iowayesterday.txt</code>

<p>Provides IEM computed totals for Iowa airport weather stations.
<a href="maxcsv/iowayesterday.txt">maxcsv/iowayesterday.txt Example</a></p>
</div>

<div class="well">
<h4>Iowa Airport data for today</h4>

<code>https://mesonet.agron.iastate.edu/request/maxcsv/iowatoday.txt</code>

<p>Provides IEM computed totals for Iowa airport weather stations.
<a href="maxcsv/iowatoday.txt">maxcsv/iowatoday.txt Example</a></p>
</div>

<div class="well">
<h4>KCRG-TV CityCam Telemetry</h4>

<code>https://mesonet.agron.iastate.edu/request/maxcsv/kcrgcitycam.txt</code>

<p>Metadata for current KCRG-TV webcams.
<a href="maxcsv/kcrgcitycam.txt">maxcsv/kcrgcitycam.txt Example</a></p>
</div>

<div class="well">
<h4>Local Storm Reports (LSR): Recent Snowfall LSRs</h4>

<code>https://mesonet.agron.iastate.edu/request/maxcsv/lsrsnowfall.txt</code>

<p>Provides any recent (past 24 hours) snowfall reports provided by the NWS
within their LSR products.
<a href="maxcsv/lsrsnowfall.txt">maxcsv/lsrsnowfall.txt Example</a></p>
</div>

<div class="well">
<h4>Local Storm Reports (LSR): Recent Snowfall LSRs by state</h4>

<code>https://mesonet.agron.iastate.edu/request/maxcsv/lsrsnowfall_ia.txt</code>

<p>Provides any recent (past 24 hours) snowfall reports provided by the NWS
within their LSR products by state.  Substitute the state abbreviation for IA.
<a href="maxcsv/lsrsnowfall_ia.txt">maxcsv/lsrsnowfall_ia.txt Example</a></p>
</div>


<div class="well">
<h4>UV Index Data</h4>

<code>https://mesonet.agron.iastate.edu/request/maxcsv/uvi.txt</code>

<p>Recoding of the <a href="https://www.cpc.ncep.noaa.gov/products/stratosphere/uv_index/bulletin.txt">CPC UVI Bulletin</a>.
<a href="maxcsv/uvi.txt">maxcsv/uvi.txt Example</a></p>
</div>

<div class="well">
<h4>Moon Phase</h4>

<code>https://mesonet.agron.iastate.edu/request/maxcsv/moonphase_\$LON_\$LAT.txt</code>

<p>Provides the dates of the next 4 moon phases.
<a href="maxcsv/moonphase_-95.44_41.99.txt">maxcsv/moonphase_-95.44_41.99.txt Example</a></p>
</div>

<div class="well">
<h4>Moon Rise/Set Phase Information</h4>

<code>https://mesonet.agron.iastate.edu/request/maxcsv/moon_\$LON_\$LAT.txt</code>

<p>Provides current moon information for the specified lon/lat value.
<a href="maxcsv/moonphase_-95.44_41.99.txt">maxcsv/moonphase_-95.44_41.99.txt Example</a></p>
</div>

<div class="well">
<h4>Month to Date Summary Information</h4>

<code>https://mesonet.agron.iastate.edu/request/maxcsv/monthlysummary_\$station_\$year_\$month.txt</code>

<p>Using a four character station identifier, provide a summary of the given month.  This is only
available for <a href="/nws/clitable.php">NWS CLI</a> reporting sites.
<a href="maxcsv/monthlysummary_KCID_2024_1.txt">maxcsv/monthlysummary_KCID_2024_1.txt Example</a></p>
</div>


EOF;
$t->render('single.phtml');
