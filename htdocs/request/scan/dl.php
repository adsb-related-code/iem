<?php
require_once "../../../config/settings.inc.php";
require_once "../../../include/database.inc.php";
require_once "../../../include/network.php";
require_once "../../../include/forms.php";
$nt = new NetworkTable("SCAN");
$cities = $nt->table;

$delim = isset($_GET["delim"]) ? xssafe($_GET["delim"]) : ",";
$sample = isset($_GET["sample"]) ? xssafe($_GET["sample"]) : "1min";
$what = isset($_GET["what"]) ? xssafe($_GET["what"]) : 'dl';

$day1 = isset($_GET["day1"]) ? xssafe($_GET["day1"]) : die("No day1 specified");
$day2 = isset($_GET["day2"]) ? xssafe($_GET["day2"]) : die("No day2 specified");
$month1 = isset($_GET["month1"]) ? xssafe($_GET["month1"]) : die("No month1 specified");
$month2 = isset($_GET["month2"]) ? xssafe($_GET["month2"]) : die("No month2 specified");
$year = isset($_GET["year"]) ? xssafe($_GET["year"]) : die("No year specified");
$hour1 = isset($_GET["hour1"]) ? xssafe($_GET["hour1"]) : die("No hour1 specified");
$hour2 = isset($_GET["hour2"]) ? xssafe($_GET["hour2"]) : die("No hour2 specified");
$minute1 = isset($_GET["minute1"]) ? xssafe($_GET["minute1"]) : die("No minute1 specified");
$minute2 = isset($_GET["minute2"]) ? xssafe($_GET["minute2"]) : die("No minute2 specified");
$vars = isset($_GET["vars"]) ? xssafe($_GET["vars"]) : die("No vars specified");

$station = $_GET["station"];
$stations = $_GET["station"];
$stationString = "(";
$selectAll = false;
foreach ($stations as $key => $value) {
    if ($value == "_ALL") {
        $selectAll = true;
    }
    $stationString .= " '" . $value . "',";
}


if ($selectAll) {
    $stationString = "(";
    foreach ($Rcities as $key => $value) {
        $stationString .= " '" . $key . "',";
    }
}

$stationString = substr($stationString, 0, -1);
$stationString .= ")";

if (isset($_GET["day"]))
    die("Incorrect CGI param, use day1, day2");

$ts1 = mktime($hour1, $minute1, 0, $month1, $day1, $year) or
    die("Invalid Date Format");
$ts2 = mktime($hour2, $minute2, 0, $month2, $day2, $year) or
    die("Invalid Date Format");

if ($selectAll && $day1 != $day2)
    $ts2 = $ts1 + 86400;

$num_vars = count($vars);
if ($num_vars == 0)  die("You did not specify data");

$sqlStr = "SELECT station, ";
for ($i = 0; $i < $num_vars; $i++) {
    $sqlStr .= $vars[$i] . " as var" . $i . ", ";
}

$sqlTS1 = date("Y-m-d H:i", $ts1);
$sqlTS2 = date("Y-m-d H:i", $ts2);
$table = sprintf("t%s", date("Y", $ts1));
$nicedate = date("Y-m-d", $ts1);

$sampleStr = array(
    "1min" => "1",
    "5min" => "5",
    "10min" => "10",
    "20min" => "20",
    "1hour" => "60"
);

$d = array("space" => " ", "comma" => ",", "tab" => "\t");

$sqlStr .= "to_char(valid, 'YYYY-MM-DD HH24:MI') as dvalid from " . $table;
$sqlStr .= " WHERE valid >= '" . $sqlTS1 . "' and valid <= '" . $sqlTS2 . "' ";
$sqlStr .= " and station IN " . $stationString . " ORDER by valid ASC";

/**
 * Must handle different ideas for what to do...
 **/

if ($what == "download") {
    header("Content-type: application/octet-stream");
    header("Content-Disposition: attachment; filename=changeme.txt");
} else {
    header("Content-type: text/plain");
}

$connection = iemdb("scan");

$query1 = "SET TIME ZONE 'GMT'";

$result = pg_exec($connection, $query1);
$rs =  pg_exec($connection, $sqlStr);

pg_close($connection);
echo "station,station_name,valid(GMT),";
for ($j = 0; $j < $num_vars; $j++) {
    echo $vars[$j] . $d[$delim];
    if ($vars[$j] == "ca1") echo "ca1code" . $d[$delim];
    if ($vars[$j] == "ca2") echo "ca2code" . $d[$delim];
    if ($vars[$j] == "ca3") echo "ca3code" . $d[$delim];
}
echo "\n";

for ($i = 0; $row = pg_fetch_array($rs); $i++) {
    $sid = $row["station"];
    echo $sid . $d[$delim] . $cities["S" . $sid]["name"];
    echo $d[$delim] . $row["dvalid"] . $d[$delim];
    for ($j = 0; $j < $num_vars; $j++) {
        echo $row["var" . $j] . $d[$delim];
    }
    echo "\n";
}
