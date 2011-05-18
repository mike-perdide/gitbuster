UI = $(wildcard *.ui)
UIPY = $(UI:.ui=_ui.py)

QRC = $(wildcard *.qrc)
RCPY = $(QRC:.qrc=_rc.py)

OBJECTS = $(RCPY) $(UIPY)

%_ui.py: %.ui
	pyuic4 $< -o $@

%_rc.py: %.qrc
	pyrcc4 $< -o $@

all: $(OBJECTS)

clean:
	rm -f $(UIPY)
	rm -f $(RCPY)
	rm -f *.pyc

test:
	@echo we need to write tests
	@fail
