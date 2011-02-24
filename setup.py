#!/usr/bin/env python
from distutils.core import setup
import ConfigParser

SETUP_ARGS = {"name"        : ("metadata",),
              "version"     : ("metadata",),
              "description" : ("metadata", "summary"),
              "author"      : ("metadata",),
              "author_email": ("metadata",),
              "keywords"    : ("metadata",),
              "url"         : ("metadata", "home_page"),
              "license"     : ("metadata",),
              "packages"    : ("files",),
              "requires"    : ("metadata", "requires_dist"),
              "classifiers" : ("metadata", "classifier"),
              "scripts"     : ("files",),
             }

MULTI = ("classifiers",
         "requires",
         "packages",
         "scripts")

def generate_setuptools_kwargs_from_setup_cfg():
    config = ConfigParser.RawConfigParser()
    config.read('setup.cfg')

    kwargs = {}
    for arg in SETUP_ARGS:
        if len(SETUP_ARGS[arg]) == 2:
            section, option = SETUP_ARGS[arg]

        elif len(SETUP_ARGS[arg]) == 1:
            section = SETUP_ARGS[arg][0]
            option = arg

        try:
            in_cfg_value = config.get(section, option)
        except ConfigParser.NoOptionError, e:
            # There is no such option in the setup.cfg
            continue

        if arg in MULTI:
            # Special behaviour when we have a multi line option
            if "\n" in in_cfg_value:
                in_cfg_value = in_cfg_value.strip().split('\n')
            else:
                in_cfg_value = list((in_cfg_value,))

        kwargs[arg] = in_cfg_value

    return kwargs
    
#from pprint import pprint
kwargs = generate_setuptools_kwargs_from_setup_cfg()
setup(**kwargs)
