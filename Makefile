UI = $(wildcard gitbuster/*.ui)
UIPATCH = $(wildcard  gitbuster/*_ui.patch)
UIPY = $(UI:.ui=_ui.py)
PYUIC4 = pyuic4

QRC = $(wildcard gitbuster/*.qrc)
RCPY = $(QRC:.qrc=_rc.py)
PYRCC4 = pyrcc4

objects = ${UIPY} ${RCPY}

all:		${objects}

$(UIPY):	$(UI)
	$(foreach ui,$(UI), $(PYUIC4) $(ui) -o $(ui:.ui=_ui.py);)


${RCPY}: ${QRC}
	$(foreach rc,$(QRC), $(PYRCC4) $(rc) -o $(rc:.qrc=_rc.py);)

clean:
	rm -f $(UIPY)
	rm -f ${RCPY}
	rm -f *.pyc

install:	${all}
	python -m "distutils2.run" install_dist||python setup.py install

publish:	${all}
	python -m "distutils2.run" register sdist upload
