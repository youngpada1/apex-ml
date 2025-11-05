#!/bin/bash
# Script to generate RSA key pair for Snowflake authentication
# This follows industry best practices for secure authentication

set -e

echo "🔐 Snowflake Key Pair Authentication Setup"
echo "=========================================="
echo ""

# Create .ssh directory if it doesn't exist
mkdir -p ~/.ssh

# Generate private key
echo "Generating RSA private key..."
openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out ~/.ssh/snowflake_key.p8 -nocrypt

# Generate public key from private key
echo "Generating public key..."
openssl rsa -in ~/.ssh/snowflake_key.p8 -pubout -out ~/.ssh/snowflake_key.pub

# Set proper permissions
chmod 600 ~/.ssh/snowflake_key.p8
chmod 644 ~/.ssh/snowflake_key.pub

echo ""
echo "✅ Keys generated successfully!"
echo ""
echo "Private key: ~/.ssh/snowflake_key.p8"
echo "Public key: ~/.ssh/snowflake_key.pub"
echo ""
echo "📋 Next Steps:"
echo "=============="
echo ""
echo "1. Copy the public key below and add it to your Snowflake user:"
echo ""
cat ~/.ssh/snowflake_key.pub | grep -v "BEGIN PUBLIC KEY" | grep -v "END PUBLIC KEY" | tr -d '\n'
echo ""
echo ""
echo "2. Run this SQL in Snowflake (replace YOUR_USERNAME):"
echo ""
echo "ALTER USER YOUR_USERNAME SET RSA_PUBLIC_KEY='<paste the key above>';"
echo ""
echo "3. Set environment variables in your shell:"
echo ""
echo "export SNOWFLAKE_ACCOUNT='your-account-identifier'"
echo "export SNOWFLAKE_USER='your-username'"
echo "export SNOWFLAKE_PRIVATE_KEY_PATH='\$HOME/.ssh/snowflake_key.p8'"
echo ""
echo "4. Add to ~/.bashrc or ~/.zshrc to make permanent"
echo ""
