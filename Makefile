VERSION             =  "2024.08.09"
AUTHOR              =  "EpicMorg"
MODIFIED            =  "STAM"
PIP_BREAK_SYSTEM_PACKAGES=1

app:
	@make -s version
	@make -s help

version:
	@echo "=================================================="
	@echo " make script, version: ${VERSION}, [` git branch --show-current `]"
	@echo "=================================================="

help:
	@echo "make help                         - show this help."
	@echo "make version                      - show version of this repository."
	@echo "make pip                          - install requerments."
	@echo "make build                        - build dist."
	@echo "make deploy                       - upload to pupy.org."
	@echo "make build-and-deploy             - alias to build and deploy."

pip:
	rm -rf /usr/lib/python3.6/EXTERNALLY-MANAGED
	rm -rf /usr/lib/python3.7/EXTERNALLY-MANAGED
	rm -rf /usr/lib/python3.8/EXTERNALLY-MANAGED
	rm -rf /usr/lib/python3.9/EXTERNALLY-MANAGED
	rm -rf /usr/lib/python3.9/EXTERNALLY-MANAGED
	rm -rf /usr/lib/python3.11/EXTERNALLY-MANAGED
	rm -rf /usr/lib/python3.12/EXTERNALLY-MANAGED
	rm -rf /usr/lib/python3.13/EXTERNALLY-MANAGED
	pip3 install -r requirements.txt
	pip install -r requirements.txt

build:
	python3 -m build 

deploy:
	twine upload dist/*

build-and-deploy:
	make build
	make deploy
