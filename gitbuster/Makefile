PY = $(wildcard *.py)
PY_REORDERED = $(PY:.py=_py_reorder_imports)
UI = $(wildcard *.ui)
UIPY = $(UI:.ui=_ui.py)

QRC = $(wildcard *.qrc)
RCPY = $(QRC:.qrc=_rc.py)

OBJECTS = $(RCPY) $(UIPY)

%_ui.py: %.ui
	pyuic4 $< -o $@

%_rc.py: %.qrc
	pyrcc4 $< -o $@

%_py_reorder_imports: %.py
	reorder -i $< -o $<

reorder_imports: $(PY_REORDERED)

all: $(OBJECTS)

clean:
	rm -f $(UIPY)
	rm -f $(RCPY)
	rm -f *.pyc

test:
	@echo we need to write tests
	@fail
