run:
	python3 -m src.main config.csv
	
test:
	python3 -m unittest discover -s tests
