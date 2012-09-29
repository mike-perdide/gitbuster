PY = $(wildcard *.py)
PY_TESTED = $(PY:.py=_py_tested)
UI = $(wildcard *.ui)
UIPY = $(UI:.ui=_ui.py)
QRC = $(wildcard *.qrc)
RCPY = $(QRC:.qrc=_rc.py)
OBJECTS = $(RCPY) $(UIPY)
RESOURCES = $(wildcard images/*)

all: $(OBJECTS)

clean:
	rm -f $(UIPY)
	rm -f $(RCPY)
	rm -f *.pyc

test: $(PY_TESTED)
	@echo Write mooooooore tests!

$(RCPY): $(RESOURCES)

%_ui.py: %.ui
	pyuic4 $< -o $@

%_rc.py: %.qrc
	pyrcc4 $< -o $@

%_py_tested: %.py
	PYTHONPATH=$(SRC_ROOT) python -m doctest $<

