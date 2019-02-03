bump-patch:
	bumpversion patch

bump-minor:
	bumpversion minor

start-dev:
	@LOG_LEVEL=debug &&  /usr/bin/env python3 -m "$${PWD##*/}"

clean:
	find . -name "*.pyc" -exec rm -f "{}" \;

run:
	curl "host:10000/run/$${PWD##*/}" | jq

rm:
	curl "host:10000/rm/$${PWD##*/}" | jq
