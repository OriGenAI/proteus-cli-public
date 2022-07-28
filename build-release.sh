git ls-files --recurse-submodules | grep -v requirements/preprocessing/tests/files | tar vcaf ../proteus-cli.tar.gz -T-
