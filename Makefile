include docker/.env

BUILD_PRINT = \e[1;34mSTEP: \e[0m

#-----------------------------------------------------------------------------
# Basic commands
#-----------------------------------------------------------------------------

install:
	@ echo "$(BUILD_PRINT)Installing the requirements"
	@ pip install --upgrade pip
	@ pip install update
	@ pip install -r requirements.txt
	@ pip install -r requirements-dev.txt

test:
	@ echo "$(BUILD_PRINT)Running the tests"
	@ pytest

#-----------------------------------------------------------------------------
# Fuseki related commands
#-----------------------------------------------------------------------------

start-fuseki:
	@ echo "$(BUILD_PRINT)Starting Fuseki on port $(if $(RDF_FINGERPRINTER_FUSEKI_PORT),$(RDF_FINGERPRINTER_FUSEKI_PORT),'default port')"
	@ docker-compose --file docker/docker-compose.yml --env-file docker/.env up -d fuseki

stop-fuseki:
	@ echo "$(BUILD_PRINT)Stopping Fuseki"
	@ docker-compose --file docker/docker-compose.yml --env-file docker/.env down

fuseki-create-test-dbs: start-fuseki
	@ echo "$(BUILD_PRINT) Uploading the datasets"
	@ sleep 3
	@ curl -X DELETE --anyauth --user 'admin:admin' http://localhost:$(RDF_FINGERPRINTER_FUSEKI_PORT)/dev/data
	@ curl --anyauth --user 'admin:admin' -d 'dbType=tdb&dbName=dev'  http://localhost:$(RDF_FINGERPRINTER_FUSEKI_PORT)/$$/datasets
	@ curl -X POST -H content-type:application/rdf+xml -T tests/test_data/continents-source-ap.rdf -G http://localhost:$(RDF_FINGERPRINTER_FUSEKI_PORT)/dev/data --data-urlencode 'graph=http://publications.europa.eu/resources/authority/continents'
	@ curl -X POST -H content-type:application/rdf+xml -T tests/test_data/treaties-source-ap.rdf -G http://localhost:$(RDF_FINGERPRINTER_FUSEKI_PORT)/dev/data --data-urlencode 'graph=http://publications.europa.eu/resources/authority/treaties'
	@ curl -X POST -H content-type:application/rdf+xml -T ./tests/test_data/continents-source-ap.rdf -G http://localhost:$(RDF_FINGERPRINTER_FUSEKI_PORT)/dev/data

#-----------------------------------------------------------------------------
# Publishing to PIPY
#-----------------------------------------------------------------------------

publish-pipy:
	@ echo "$(BUILD_PRINT)Creating the source distribution"
	@ python3 setup.py sdist bdist_wheel
	@ echo "$(BUILD_PRINT)Checking the distribution"
	@ twine check dist/*
	@ echo "$(BUILD_PRINT)Uploading the distribution"
	@ twine upload --skip-existing dist/*
