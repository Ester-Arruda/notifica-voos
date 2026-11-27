status=0
python monitor.py || status=1
python chamar_scraper.py || status=1
exit $status