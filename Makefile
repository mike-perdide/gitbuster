SRCDIRS = gitbuster
GENTARGETS = all clean test

$(GENTARGETS): $(SRCDIRS)
	#Make recursion
	$(MAKE) -C $< $@

install:	all
	pysetup run install_dist||python setup.py install

publish:	all
	pysetup run register sdist upload
