setup:
	python3 -m pip install --upgrade pip
	python3 -m pip install -r requirements.txt

check:
	python3 -m py_compile FoundationsOfAgenticTool/main.py 