#!/bin/bash

# Playwright E2E Test Setup Script
# This script sets up and runs the Playwright E2E tests

set -e

echo "=========================================="
echo "Playwright E2E Test Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is not installed${NC}"
    echo "Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node -v)
echo -e "${GREEN}✓${NC} Node.js version: $NODE_VERSION"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo -e "${RED}Error: npm is not installed${NC}"
    exit 1
fi

NPM_VERSION=$(npm -v)
echo -e "${GREEN}✓${NC} npm version: $NPM_VERSION"

echo ""
echo "Installing Node.js dependencies..."
npm install

echo ""
echo "Installing Playwright browsers..."
npx playwright install

echo ""
echo -e "${GREEN}=========================================="
echo "Setup Complete!"
echo "==========================================${NC}"
echo ""
echo "Available commands:"
echo ""
echo "  npm test              - Run all tests"
echo "  npm run test:headed   - Run tests with visible browser"
echo "  npm run test:ui       - Run tests in interactive UI mode"
echo "  npm run test:debug    - Run tests in debug mode"
echo "  npm run test:report   - Show test report"
echo ""
echo "Test files location:"
echo "  tests/e2e/register.spec.ts"
echo "  tests/e2e/login.spec.ts"
echo ""
echo -e "${YELLOW}Note: Make sure the FastAPI application is running on http://localhost:8000${NC}"
echo "      The tests will auto-start it if not running."
echo ""
