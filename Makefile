UI=$(wildcard gitbuster/*.ui)
UIPATCH=$(wildcard  gitbuster/*_ui.patch)
UIPY=$(UI:.ui=_ui.py)
PYUIC4=pyuic4

all:		$(UIPY)

$(UIPY):	$(UI)
	$(foreach ui,$(UI), $(PYUIC4) $(ui) -o $(ui:.ui=_ui.py);)

clean:
	rm -f $(UIPY)
	rm -f *.pyc

install:
	python -m "distutils2.run" install_dist||python setup.py install

publish:	$(UIPY)
	python -m "distutils2.run" register sdist upload
