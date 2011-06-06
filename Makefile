SRCDIRS = gitbuster
GENTARGETS = all clean test

$(GENTARGETS): $(SRCDIRS)
	#Make recursion
	$(MAKE) -C $< $@

install:	all
	$(MAKE) install -C gfbi_core
	pysetup run install_dist||python setup.py install

publish:	all
	pysetup run register sdist upload

update-code:
	#Violent.
	git pull --rebase
	git submodule init
	git submodule update
