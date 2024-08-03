.PHONY: build
build:
	rm dist/*
	python3 -m build
	# python3 setup.py bdist_wheel
	# python3 setup.py sdist

.PHONY: check
check:
	twine check dist/*

.PHONY: publish
publish:
	twine upload --username __token__ --password `op read "op://Rob/pypi/apikey"` dist/*