#!/bin/bash
# Get depletion chain file

CHAIN_FILE="chain_simple.xml"
SOURCE_PATH="../pincell_depletion/${CHAIN_FILE}"

echo "Setting up depletion chain file for derivative_depletion example"
echo "================================================================"
echo ""

# Check if chain file already exists
if [ -f "$CHAIN_FILE" ]; then
    echo "Chain file already exists: $CHAIN_FILE"
    exit 0
fi

# Try to copy from pincell_depletion example
if [ -f "$SOURCE_PATH" ]; then
    echo "Copying chain file from pincell_depletion example..."
    cp "$SOURCE_PATH" . || {
        echo "Error: Failed to copy chain file"
        exit 1
    }
    echo "Successfully copied $CHAIN_FILE"
    exit 0
fi

# If that doesn't work, try to find it in tests directory
TEST_PATH="../../tests/chain_simple.xml"
if [ -f "$TEST_PATH" ]; then
    echo "Copying chain file from tests directory..."
    cp "$TEST_PATH" . || {
        echo "Error: Failed to copy chain file"
        exit 1
    }
    echo "Successfully copied $CHAIN_FILE"
    exit 0
fi

# If we get here, we couldn't find the file
echo "Error: Could not find chain_simple.xml"
echo ""
echo "Please copy it manually:"
echo "  cp ../pincell_depletion/chain_simple.xml ."
echo ""
echo "Or from the OpenMC tests directory:"
echo "  cp ../../tests/chain_simple.xml ."
exit 1
