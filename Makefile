-include appstore/Makefile

VERSION=1.0.1
SRC_CORE=src
SRC_TEST=tests
PYTHON=python3
PYDOC=pydoc3
PIP=pip3
.PHONY: test clean run doc

help:
	@echo "Some available commands:"
	@echo " * run          - Run code."
	@echo " * test         - Run unit tests and test coverage."
	@echo " * doc          - Document code (pydoc)."
	@echo " * clean        - Cleanup (e.g. pyc files)."
	@echo " * auto-style   - Automatially style code (autopep8)."
	@echo " * code-style   - Check code style (pycodestyle)."
	@echo " * code-lint    - Check code lints (pyflakes, pyline, flake8)."
	@echo " * code-count   - Count code lines (cloc)."
	@echo " * deps-install - Install dependencies (see requirements.txt)."
	@echo " * deps-update  - Update dependencies (pur)."
	@echo " * deps-create  - Create dependencies (pipreqs)."
	@echo " * feedback     - Create a GitHub issue."

run:
	@$(PYTHON) -m $(SRC_CORE).mailbox_cli --help

test:
	@type coverage >/dev/null 2>&1 || (echo "Run '$(PIP) install coverage' first." >&2 ; exit 1)
	@coverage run --source . -m unittest discover
	@coverage report

doc:
	@$(PYDOC) src.mailbox_cli

clean:
	@rm -f $(SRC_CORE)/*.pyc
	@rm -rf $(SRC_CORE)/__pycache__
	@rm -f $(SRC_TEST)/*.pyc
	@rm -rf $(SRC_TEST)/__pycache__
	@rm -rf htmlcov
	@rm -rf dist
	@rm -rf build

auto-style:
	@type autopep8 >/dev/null 2>&1 || (echo "Run '$(PIP) install autopep8' first." >&2 ; exit 1)
	@autopep8 -i -r $(SRC_CORE)

code-style:
	@type pycodestyle >/dev/null 2>&1 || (echo "Run '$(PIP) install pycodestyle' first." >&2 ; exit 1)
	@pycodestyle --max-line-length=80 $(SRC_CORE)

code-lint:
	@type pyflakes >/dev/null 2>&1 || (echo "Run '$(PIP) install pyflakes' first." >&2 ; exit 1)
	@type pylint >/dev/null 2>&1 || (echo "Run '$(PIP) install pylint' first." >&2 ; exit 1)
	@type flake8 >/dev/null 2>&1 || (echo "Run '$(PIP) install flake8' first." >&2 ; exit 1)
	@pyflakes $(SRC_CORE) $(SRC_TEST)
	@pylint $(SRC_CORE) $(SRC_TEST)
	@flake8 --max-complexity 10 $(SRC_CORE) $(SRC_TEST)

code-count:
	@type cloc >/dev/null 2>&1 || (echo "Run 'brew install cloc' first." >&2 ; exit 1)
	@cloc $(SRC_CORE)

lint: code-style code-lint

deps-update:
	@type pur >/dev/null 2>&1 || (echo "Run '$(PIP) install pur' first." >&2 ; exit 1)
	@pur -r requirements.txt

deps-install:
	@type $(PIP) >/dev/null 2>&1 || (echo "Run 'curl https://bootstrap.pypa.io/get-pip.py|sudo python3' first." >&2 ; exit 1)
	@$(PIP) install -r requirements.txt

deps-create:
	@type pipreqs >/dev/null 2>&1 || (echo "Run '$(PIP) install pipreqs' first." >&2 ; exit 1)
	@pipreqs --use-local --force .

feedback:
	@open https://github.com/AlexanderWillner/MailboxCleanup/issues

commit: test auto-style lint
	@git status

version:
	@read -p "Press CTRL+C to NOT making release $(VERSION)..."
	@sed -i '' 's/VERSION = ".*"/VERSION = "'$(VERSION)'"/g' appstore/setup.py
	@find src/ -type f -iname "*.py" -execdir sed -i '' 's/__version__ = ".*"/__version__ = "'$(VERSION)'"/g' {} \;
