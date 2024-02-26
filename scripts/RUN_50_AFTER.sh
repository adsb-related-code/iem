# cronscript for 50 minutes after the hour

python cache/cache_autoplots.py &

python dl/download_rtma_ru.py &

cd gfs
python gfs2iemre.py $(date -u --date '7 hours ago' +'%Y %m %d %H') &

cd ../ingestors/madis
python extract_hfmetar.py 2 &

# Run HRRR radiation ingest at 10 PM, so that we have this available
# for ISUSM et al
HH=$(date +%H)
if [ "$HH" -eq "22" ]
    then
        cd ../../climodat
        python hrrr_solarrad.py --date=$(date +'%Y-%m-%d')	
fi

# END