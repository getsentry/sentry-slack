publish:
	python setup.py sdist upload

clean:
	rm -rf *.egg-info
	rm -rf dist

.PHONY: publish clean