SRCDIRS = gitbuster
GENTARGETS = all clean test

$(GENTARGETS): $(SRCDIRS)
	#Make recursion
	$(MAKE) -C $< $@

install:	all
	python -m "distutils2.run" install_dist||python setup.py install

publish:	all
	python -m "distutils2.run" register sdist upload
