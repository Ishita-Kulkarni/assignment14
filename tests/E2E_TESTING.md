# Playwright E2E Tests Documentation

Comprehensive end-to-end testing suite for the FastAPI authentication system using Playwright.

## 📋 Test Coverage

### Registration Tests (Positive)
- ✅ Register with valid data (username, email, password)
- ✅ Verify success message displayed
- ✅ Confirm JWT token stored in localStorage
- ✅ Verify user data stored correctly
- ✅ Check password strength indicator (weak/medium/strong)
- ✅ Validate email format acceptance
- ✅ Verify minimum password length (8 characters)
- ✅ Test redirect to home page after registration

### Registration Tests (Negative)
- ✅ Short username (< 3 characters) → Show error
- ✅ Long username (> 50 characters) → Show error
- ✅ Invalid email format → Show error
- ✅ Short password (< 8 characters) → Show error
- ✅ Mismatched passwords → Show error
- ✅ Empty form submission → Show error
- ✅ Duplicate username → Server returns 400, UI shows error
- ✅ Duplicate email → Server returns 400, UI shows error
- ✅ Already logged in users redirected

### Login Tests (Positive)
- ✅ Login with valid username and password
- ✅ Login with email instead of username
- ✅ Verify success message displayed
- ✅ Confirm JWT token stored in sessionStorage (default)
- ✅ "Remember Me" checked → Token in localStorage
- ✅ "Remember Me" unchecked → Token in sessionStorage
- ✅ Verify redirect to home page after login
- ✅ Check user data stored correctly

### Login Tests (Negative)
- ✅ Empty username → Show error
- ✅ Empty password → Show error
- ✅ Wrong password → Server returns 401, UI shows "Invalid credentials"
- ✅ Non-existent user → Server returns 401, UI shows "Invalid credentials"
- ✅ Password field cleared after failed login
- ✅ Submit button re-enabled after error
- ✅ Network errors handled gracefully
- ✅ Already logged in users redirected

## 🚀 Quick Start

### Install Dependencies
```bash
# Install Node.js dependencies
npm install

# Install Playwright browsers
npx playwright install
```

### Run Tests
```bash
# Run all tests
npm test

# Run in headed mode (watch browser)
npm run test:headed

# Run in UI mode (interactive)
npm run test:ui

# Run specific browser
npm run test:chromium
npm run test:firefox
npm run test:webkit
```

### View Reports
```bash
npm run test:report
```

## 📊 Test Files

- `tests/e2e/register.spec.ts` - Registration flow tests (20+ tests)
- `tests/e2e/login.spec.ts` - Login flow tests (20+ tests)

## 🎯 Key Test Scenarios

### ✅ Successful Registration
1. Navigate to register page
2. Fill valid data
3. Submit form
4. Verify success message
5. Verify JWT token stored
6. Verify redirect

### ❌ Registration with Short Password
1. Navigate to register page
2. Fill password < 8 chars
3. Submit form
4. Verify error message
5. Verify no token stored

### ✅ Successful Login
1. Register test user
2. Navigate to login page
3. Enter credentials
4. Submit form
5. Verify success + token
6. Verify redirect

### ❌ Login with Wrong Password
1. Register test user
2. Login with wrong password
3. Verify 401 error
4. Verify error message
5. Verify no token stored

## 🛠️ Available Scripts

```json
{
  "test": "Run all tests",
  "test:headed": "Run tests with visible browser",
  "test:ui": "Run tests in interactive UI mode",
  "test:debug": "Run tests in debug mode",
  "test:chromium": "Run tests in Chromium only",
  "test:firefox": "Run tests in Firefox only",
  "test:webkit": "Run tests in WebKit only",
  "test:report": "Show HTML test report"
}
```

## 🔧 Configuration

Tests are configured to:
- Run against `http://localhost:8000`
- Auto-start FastAPI server if not running
- Capture screenshots on failure
- Record videos on failure
- Generate HTML reports

## 📝 Writing New Tests

```typescript
import { test, expect } from '@playwright/test';

test('should do something', async ({ page }) => {
  await page.goto('/static/register.html');
  await page.fill('#username', 'testuser');
  await page.click('button[type="submit"]');
  
  await expect(page.locator('.alert-success')).toBeVisible();
});
```

## 🐛 Debugging

```bash
# Debug mode with inspector
npm run test:debug

# UI mode for visual debugging
npm run test:ui

# Generate test code
npm run test:codegen
```

## 📈 Test Metrics

- **Total Tests:** 40+
- **Registration Tests:** 20+
- **Login Tests:** 20+
- **Browsers Tested:** Chrome, Firefox, Safari, Mobile

For detailed documentation, see the inline comments in test files.
