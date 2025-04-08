#!/bin/bash

# Check if bucket name is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <bucket-name>"
    exit 1
fi

BUCKET_NAME=$1
TEMP_DIR="s3_download_temp"
OUTPUT_ZIP="bucket_contents.zip"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Create temporary directory
echo "Creating temporary directory..."
mkdir -p "$TEMP_DIR"

# Download all contents from S3 bucket
echo "Downloading contents from s3://$BUCKET_NAME..."
aws s3 sync "s3://$BUCKET_NAME" "$TEMP_DIR"

# Check if download was successful
if [ $? -eq 0 ]; then
    # Create zip file
    echo "Creating zip file..."
    zip -r "$OUTPUT_ZIP" "$TEMP_DIR"

    # Clean up temporary directory
    echo "Cleaning up..."
    rm -rf "$TEMP_DIR"

    echo "Done! Contents have been downloaded and zipped to $OUTPUT_ZIP"
else
    echo "Error downloading from S3 bucket"
    rm -rf "$TEMP_DIR"
    exit 1
fi
