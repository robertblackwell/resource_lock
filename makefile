.PHONY: build
build:
	rm dist/*
	python3 setup.py bdist_wheel
	python3 setup.py sdist

.PHONY: check
check:
	twine check dist/*

.PHONY: publish
publish:
	twine upload dist/*