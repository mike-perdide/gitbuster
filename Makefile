install:
	python -m "distutils2.run" install_dist||python setup.py install

publish:
	python -m "distutils2.run" register sdist upload
