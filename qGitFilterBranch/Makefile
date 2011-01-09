UI=$(wildcard *.ui)
UIPATCH=$(wildcard *_ui.patch)
UIPY=$(UI:.ui=_ui.py)
PYUIC4=pyuic4

all:		$(UIPY)

$(UIPY):	$(UI)
	$(foreach ui,$(UI), $(PYUIC4) $(ui) -o $(ui:.ui=_ui.py);)

clean:
	rm -f $(UIPY)
	rm -f *.pyc

