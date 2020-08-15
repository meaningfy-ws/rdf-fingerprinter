.PHONY: test install lint generate-tests-from-features

include .env-dev

BUILD_PRINT = \e[1;34mSTEP: \e[0m

#-----------------------------------------------------------------------------
# Basic commands
#-----------------------------------------------------------------------------

install:
	@ echo "$(BUILD_PRINT)Installing the requirements"
	@ pip install --upgrade pip
	@ pip install -r requirements.txt
	@ pip install -r requirements-dev.txt

lint:
	@ echo "$(BUILD_PRINT)Linting the code"
	@ flake8 || true

test:
	@ echo "$(BUILD_PRINT)Running the tests"
	@ pytest || true

#-----------------------------------------------------------------------------
# Gherkin feature and acceptance tests generation commands
#-----------------------------------------------------------------------------

FEATURES_FOLDER = tests/features
STEPS_FOLDER = tests/steps
FEATURE_FILES := $(wildcard $(FEATURES_FOLDER)/*.feature)
EXISTENT_TEST_FILES = $(wildcard $(STEPS_FOLDER)/*.py)
HYPOTHETICAL_TEST_FILES :=  $(addprefix $(STEPS_FOLDER)/test_, $(notdir $(FEATURE_FILES:.feature=.py)))
TEST_FILES := $(filter-out $(EXISTENT_TEST_FILES),$(HYPOTHETICAL_TEST_FILES))

generate-tests-from-features: $(TEST_FILES)
	@ echo "$(BUILD_PRINT)The following test files should be generated: $(TEST_FILES)"
	@ echo "$(BUILD_PRINT)Done generating missing feature files"
	@ echo "$(BUILD_PRINT)Verifying if there are any missing step implementations"
	@ py.test --generate-missing --feature $(FEATURES_FOLDER)

$(addprefix $(STEPS_FOLDER)/test_, $(notdir $(STEPS_FOLDER)/%.py)): $(FEATURES_FOLDER)/%.feature
	@ echo "$(BUILD_PRINT)Generating the testfile "$@"  from "$<" feature file"
	@ pytest-bdd generate $< > $@
	@ sed -i  's|features|../features|' $@

publish-pipy:
	@ echo "$(BUILD_PRINT)Creating the source distribution"
	@ python3 setup.py sdist bdist_wheel
	@ echo "$(BUILD_PRINT)Checking the distribution"
	@ twine check dist/*
	@ echo "$(BUILD_PRINT)Uploading the distribution"
	@ twine upload --skip-existing dist/*

#-----------------------------------------------------------------------------
# Default
#-----------------------------------------------------------------------------
all: install test
