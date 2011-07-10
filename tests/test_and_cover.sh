GITBUSTER_DIR=$(python -c "import gitbuster; import os; print os.path.dirname(gitbuster.__file__)")
GFBI_CORE_DIR=$(python -c "import gfbi_core; import os; print os.path.dirname(gfbi_core.__file__)")

OMIT_UI_FILES="$GITBUSTER_DIR/*_ui.py"

coverage run --source=$GITBUSTER_DIR,$GFBI_CORE_DIR --omit=$OMIT_UI_FILES all_tests.py
coverage report --omit=$OMIT_UI_FILES
coverage html --omit=$OMIT_UI_FILES
