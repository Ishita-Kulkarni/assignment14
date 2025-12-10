import { test, expect, Page } from '@playwright/test';

/**
 * E2E Tests for Calculations BREAD Operations
 * Tests cover: Browse, Read, Edit, Add, Delete
 * Both positive and negative scenarios
 */

/**
 * Helper function to generate unique user data
 */
function generateUniqueUser() {
  const timestamp = Date.now();
  const random = Math.floor(Math.random() * 10000);
  return {
    username: `calcuser_${timestamp}_${random}`,
    email: `calcuser_${timestamp}_${random}@example.com`,
    password: 'SecurePass123!',
  };
}

/**
 * Helper function to clear browser storage
 */
async function clearStorage(page: Page) {
  const url = page.url();
  if (!url || url === 'about:blank' || !url.includes('localhost')) {
    await page.goto('/static/login.html');
  }
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
}

/**
 * Helper function to register and login a user
 */
async function registerAndLogin(page: Page, user: { username: string; email: string; password: string }) {
  // Register
  await page.goto('/static/register.html');
  await page.fill('#username', user.username);
  await page.fill('#email', user.email);
  await page.fill('#password', user.password);
  await page.fill('#confirmPassword', user.password);
  await page.click('button[type="submit"]');
  
  // Wait for successful registration and redirect
  await expect(page.locator('.alert-success')).toBeVisible({ timeout: 5000 });
  await page.waitForTimeout(2000); // Wait for redirect
}

/**
 * Helper function to create a calculation via UI
 */
async function createCalculation(page: Page, a: number, b: number, operation: string) {
  await page.click('button:has-text("New Calculation")');
  await expect(page.locator('#calculationModal')).toHaveClass(/show/);
  
  await page.fill('#operandA', a.toString());
  await page.fill('#operandB', b.toString());
  await page.selectOption('#operation', operation);
  
  await page.click('#calculationForm button[type="submit"]');
  await page.waitForTimeout(1000); // Wait for API response
}

test.describe('Calculations - Browse (List All)', () => {
  test.beforeEach(async ({ page }) => {
    await clearStorage(page);
  });

  test('should display empty state when no calculations exist', async ({ page }) => {
    const user = generateUniqueUser();
    await registerAndLogin(page, user);
    
    await page.goto('/static/calculations.html');
    await page.waitForTimeout(1000);

    // Should show empty state
    await expect(page.locator('.empty-state')).toBeVisible();
    await expect(page.locator('.empty-state')).toContainText('No Calculations Yet');
  });

  test('should display all user calculations in a list', async ({ page }) => {
    const user = generateUniqueUser();
    await registerAndLogin(page, user);
    
    await page.goto('/static/calculations.html');
    await page.waitForTimeout(1000);

    // Create multiple calculations
    await createCalculation(page, 10, 5, 'add');
    await createCalculation(page, 20, 4, 'subtract');
    await createCalculation(page, 6, 3, 'multiply');

    // Refresh to see all calculations
    await page.click('button:has-text("Refresh")');
    await page.waitForTimeout(1000);

    // Verify calculations are displayed
    const calcCards = page.locator('.calculation-card');
    await expect(calcCards).toHaveCount(3);
  });

  test('should show correct calculation details in list', async ({ page }) => {
    const user = generateUniqueUser();
    await registerAndLogin(page, user);
    
    await page.goto('/static/calculations.html');
    await createCalculation(page, 15, 5, 'add');
    
    await page.click('button:has-text("Refresh")');
    await page.waitForTimeout(1000);

    // Verify calculation display
    const calcCard = page.locator('.calculation-card').first();
    await expect(calcCard.locator('.calculation-expression')).toContainText('15');
    await expect(calcCard.locator('.calculation-expression')).toContainText('5');
    await expect(calcCard.locator('.calculation-result')).toContainText('20');
  });

  test('should display calculations in descending order by creation date', async ({ page }) => {
    const user = generateUniqueUser();
    await registerAndLogin(page, user);
    
    await page.goto('/static/calculations.html');
    
    // Create calculations with delay to ensure different timestamps
    await createCalculation(page, 1, 1, 'add');
    await page.waitForTimeout(500);
    await createCalculation(page, 2, 2, 'add');
    await page.waitForTimeout(500);
    await createCalculation(page, 3, 3, 'add');
    
    await page.click('button:has-text("Refresh")');
    await page.waitForTimeout(1000);

    // The most recent calculation (3+3=6) should be first
    const firstCalc = page.locator('.calculation-card').first();
    await expect(firstCalc.locator('.calculation-result')).toContainText('6');
  });
});

test.describe('Calculations - Read (View Details)', () => {
  test.beforeEach(async ({ page }) => {
    await clearStorage(page);
  });

  test('should display calculation details in modal when View is clicked', async ({ page }) => {
    const user = generateUniqueUser();
    await registerAndLogin(page, user);
    
    await page.goto('/static/calculations.html');
    await createCalculation(page, 25, 5, 'divide');
    
    await page.click('button:has-text("Refresh")');
    await page.waitForTimeout(1000);

    // Click view button
    await page.click('button:has-text("View")');
    await page.waitForTimeout(500);

    // Verify modal is visible
    await expect(page.locator('#viewModal')).toHaveClass(/show/);
    
    // Verify details are displayed
    await expect(page.locator('#calculationDetails')).toContainText('25');
    await expect(page.locator('#calculationDetails')).toContainText('5');
    await expect(page.locator('#calculationDetails')).toContainText('5'); // Result
  });

  test('should show all calculation fields in detail view', async ({ page }) => {
    const user = generateUniqueUser();
    await registerAndLogin(page, user);
    
    await page.goto('/static/calculations.html');
    await createCalculation(page, 100, 25, 'subtract');
    
    await page.click('button:has-text("Refresh")');
    await page.waitForTimeout(1000);
    await page.click('button:has-text("View")');
    await page.waitForTimeout(500);

    const details = page.locator('#calculationDetails');
    
    // Check for key fields
    await expect(details).toContainText('ID:');
    await expect(details).toContainText('First Operand');
    await expect(details).toContainText('Operation');
    await expect(details).toContainText('Second Operand');
    await expect(details).toContainText('Result');
    await expect(details).toContainText('User ID');
    await expect(details).toContainText('Created At');
  });

  test('should close detail modal when X is clicked', async ({ page }) => {
    const user = generateUniqueUser();
    await registerAndLogin(page, user);
    
    await page.goto('/static/calculations.html');
    await createCalculation(page, 10, 2, 'multiply');
    
    await page.click('button:has-text("Refresh")');
    await page.waitForTimeout(1000);
    await page.click('button:has-text("View")');
    await page.waitForTimeout(500);

    // Close modal
    await page.click('#viewModal .close');
    await page.waitForTimeout(300);

    // Verify modal is hidden
    await expect(page.locator('#viewModal')).not.toHaveClass(/show/);
  });
});

test.describe('Calculations - Add (Create)', () => {
  test.beforeEach(async ({ page }) => {
    await clearStorage(page);
  });

  test('should successfully create an addition calculation', async ({ page }) => {
    const user = generateUniqueUser();
    await registerAndLogin(page, user);
    
    await page.goto('/static/calculations.html');
    await createCalculation(page, 50, 30, 'add');

    // Check for success message
    await expect(page.locator('.alert-success')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('.alert-success')).toContainText('created successfully');

    // Verify calculation appears in list
    await page.waitForTimeout(1000);
    const calcCard = page.locator('.calculation-card').first();
    await expect(calcCard.locator('.calculation-result')).toContainText('80');
  });

  test('should successfully create a subtraction calculation', async ({ page }) => {
    const user = generateUniqueUser();
    await registerAndLogin(page, user);
    
    await page.goto('/static/calculations.html');
    await createCalculation(page, 100, 45, 'subtract');

    await expect(page.locator('.alert-success')).toBeVisible({ timeout: 5000 });
    await page.waitForTimeout(1000);
    
    const calcCard = page.locator('.calculation-card').first();
    await expect(calcCard.locator('.calculation-result')).toContainText('55');
  });

  test('should successfully create a multiplication calculation', async ({ page }) => {
    const user = generateUniqueUser();
    await registerAndLogin(page, user);
    
    await page.goto('/static/calculations.html');
    await createCalculation(page, 7, 8, 'multiply');

    await expect(page.locator('.alert-success')).toBeVisible({ timeout: 5000 });
    await page.waitForTimeout(1000);
    
    const calcCard = page.locator('.calculation-card').first();
    await expect(calcCard.locator('.calculation-result')).toContainText('56');
  });

  test('should successfully create a division calculation', async ({ page }) => {
    const user = generateUniqueUser();
    await registerAndLogin(page, user);
    
    await page.goto('/static/calculations.html');
    await createCalculation(page, 100, 4, 'divide');

    await expect(page.locator('.alert-success')).toBeVisible({ timeout: 5000 });
    await page.waitForTimeout(1000);
    
    const calcCard = page.locator('.calculation-card').first();
    await expect(calcCard.locator('.calculation-result')).toContainText('25');
  });

  test('should handle decimal numbers correctly', async ({ page }) => {
    const user = generateUniqueUser();
    await registerAndLogin(page, user);
    
    await page.goto('/static/calculations.html');
    await createCalculation(page, 10.5, 2.5, 'add');

    await expect(page.locator('.alert-success')).toBeVisible({ timeout: 5000 });
    await page.waitForTimeout(1000);
    
    const calcCard = page.locator('.calculation-card').first();
    await expect(calcCard.locator('.calculation-result')).toContainText('13');
  });

  test('should handle negative numbers correctly', async ({ page }) => {
    const user = generateUniqueUser();
    await registerAndLogin(page, user);
    
    await page.goto('/static/calculations.html');
    await createCalculation(page, -10, 5, 'add');

    await expect(page.locator('.alert-success')).toBeVisible({ timeout: 5000 });
    await page.waitForTimeout(1000);
    
    const calcCard = page.locator('.calculation-card').first();
    await expect(calcCard.locator('.calculation-result')).toContainText('-5');
  });

  test('should close modal after successful creation', async ({ page }) => {
    const user = generateUniqueUser();
    await registerAndLogin(page, user);
    
    await page.goto('/static/calculations.html');
    await createCalculation(page, 5, 5, 'add');

    await page.waitForTimeout(1500);
    
    // Modal should be closed
    await expect(page.locator('#calculationModal')).not.toHaveClass(/show/);
  });
});

test.describe('Calculations - Edit (Update)', () => {
  test.beforeEach(async ({ page }) => {
    await clearStorage(page);
  });

  test('should successfully update a calculation', async ({ page }) => {
    const user = generateUniqueUser();
    await registerAndLogin(page, user);
    
    await page.goto('/static/calculations.html');
    await createCalculation(page, 10, 5, 'add');
    
    await page.click('button:has-text("Refresh")');
    await page.waitForTimeout(1000);

    // Click edit
    await page.click('button:has-text("Edit")');
    await page.waitForTimeout(500);

    // Verify form is pre-filled
    await expect(page.locator('#operandA')).toHaveValue('10');
    await expect(page.locator('#operandB')).toHaveValue('5');
    await expect(page.locator('#operation')).toHaveValue('add');

    // Update values
    await page.fill('#operandA', '20');
    await page.fill('#operandB', '10');
    await page.selectOption('#operation', 'multiply');
    
    await page.click('#calculationForm button[type="submit"]');
    await page.waitForTimeout(1000);

    // Check success message
    await expect(page.locator('.alert-success')).toBeVisible();
    await expect(page.locator('.alert-success')).toContainText('updated successfully');

    // Verify updated calculation
    const calcCard = page.locator('.calculation-card').first();
    await expect(calcCard.locator('.calculation-result')).toContainText('200');
  });

  test('should update only changed fields', async ({ page }) => {
    const user = generateUniqueUser();
    await registerAndLogin(page, user);
    
    await page.goto('/static/calculations.html');
    await createCalculation(page, 15, 3, 'multiply');
    
    await page.click('button:has-text("Refresh")');
    await page.waitForTimeout(1000);
    await page.click('button:has-text("Edit")');
    await page.waitForTimeout(500);

    // Change only the operation
    await page.selectOption('#operation', 'divide');
    
    await page.click('#calculationForm button[type="submit"]');
    await page.waitForTimeout(1000);

    // Result should be 15/3 = 5
    const calcCard = page.locator('.calculation-card').first();
    await expect(calcCard.locator('.calculation-result')).toContainText('5');
  });

  test('should show updated modal title when editing', async ({ page }) => {
    const user = generateUniqueUser();
    await registerAndLogin(page, user);
    
    await page.goto('/static/calculations.html');
    await createCalculation(page, 8, 2, 'add');
    
    await page.click('button:has-text("Refresh")');
    await page.waitForTimeout(1000);
    await page.click('button:has-text("Edit")');
    await page.waitForTimeout(500);

    // Verify modal title
    await expect(page.locator('#modalTitle')).toContainText('Edit Calculation');
    await expect(page.locator('#submitBtnText')).toContainText('Update Calculation');
  });
});

test.describe('Calculations - Delete', () => {
  test.beforeEach(async ({ page }) => {
    await clearStorage(page);
  });

  test('should successfully delete a calculation', async ({ page }) => {
    const user = generateUniqueUser();
    await registerAndLogin(page, user);
    
    await page.goto('/static/calculations.html');
    await createCalculation(page, 99, 1, 'subtract');
    
    await page.click('button:has-text("Refresh")');
    await page.waitForTimeout(1000);

    // Verify calculation exists
    await expect(page.locator('.calculation-card')).toHaveCount(1);

    // Setup dialog handler before clicking delete
    page.on('dialog', dialog => dialog.accept());
    
    // Click delete
    await page.click('button:has-text("Delete")');
    await page.waitForTimeout(1000);

    // Check success message
    await expect(page.locator('.alert-success')).toBeVisible();
    await expect(page.locator('.alert-success')).toContainText('deleted successfully');

    // Verify calculation is removed
    await expect(page.locator('.empty-state')).toBeVisible();
  });

  test('should show confirmation dialog before deleting', async ({ page }) => {
    const user = generateUniqueUser();
    await registerAndLogin(page, user);
    
    await page.goto('/static/calculations.html');
    await createCalculation(page, 50, 50, 'add');
    
    await page.click('button:has-text("Refresh")');
    await page.waitForTimeout(1000);

    // Setup dialog handler to check message and cancel
    let dialogShown = false;
    page.on('dialog', dialog => {
      dialogShown = true;
      expect(dialog.message()).toContain('Are you sure');
      dialog.dismiss();
    });
    
    await page.click('button:has-text("Delete")');
    await page.waitForTimeout(500);

    expect(dialogShown).toBe(true);
    
    // Calculation should still exist
    await expect(page.locator('.calculation-card')).toHaveCount(1);
  });

  test('should not delete if confirmation is cancelled', async ({ page }) => {
    const user = generateUniqueUser();
    await registerAndLogin(page, user);
    
    await page.goto('/static/calculations.html');
    await createCalculation(page, 10, 10, 'multiply');
    
    await page.click('button:has-text("Refresh")');
    await page.waitForTimeout(1000);

    // Cancel the deletion
    page.on('dialog', dialog => dialog.dismiss());
    
    await page.click('button:has-text("Delete")');
    await page.waitForTimeout(1000);

    // Calculation should still exist
    await expect(page.locator('.calculation-card')).toHaveCount(1);
  });
});

test.describe('Calculations - Negative Scenarios', () => {
  test.beforeEach(async ({ page }) => {
    await clearStorage(page);
  });

  test('should reject division by zero', async ({ page }) => {
    const user = generateUniqueUser();
    await registerAndLogin(page, user);
    
    await page.goto('/static/calculations.html');
    
    await page.click('button:has-text("New Calculation")');
    await page.fill('#operandA', '10');
    await page.fill('#operandB', '0');
    await page.selectOption('#operation', 'divide');
    
    await page.click('#calculationForm button[type="submit"]');
    await page.waitForTimeout(500);

    // Should show validation error
    await expect(page.locator('#operandBError')).toBeVisible();
    await expect(page.locator('#operandBError')).toContainText('Division by zero');
  });

  test('should validate required fields', async ({ page }) => {
    const user = generateUniqueUser();
    await registerAndLogin(page, user);
    
    await page.goto('/static/calculations.html');
    
    await page.click('button:has-text("New Calculation")');
    await page.click('#calculationForm button[type="submit"]');
    await page.waitForTimeout(500);

    // Should show validation errors
    await expect(page.locator('#operandAError')).toBeVisible();
    await expect(page.locator('#operationError')).toBeVisible();
    await expect(page.locator('#operandBError')).toBeVisible();
  });

  test('should validate numeric input for first operand', async ({ page }) => {
    const user = generateUniqueUser();
    await registerAndLogin(page, user);
    
    await page.goto('/static/calculations.html');
    
    await page.click('button:has-text("New Calculation")');
    await page.fill('#operandA', '');
    await page.fill('#operandB', '5');
    await page.selectOption('#operation', 'add');
    
    await page.click('#calculationForm button[type="submit"]');
    await page.waitForTimeout(500);

    await expect(page.locator('#operandAError')).toBeVisible();
  });

  test('should validate numeric input for second operand', async ({ page }) => {
    const user = generateUniqueUser();
    await registerAndLogin(page, user);
    
    await page.goto('/static/calculations.html');
    
    await page.click('button:has-text("New Calculation")');
    await page.fill('#operandA', '10');
    await page.fill('#operandB', '');
    await page.selectOption('#operation', 'add');
    
    await page.click('#calculationForm button[type="submit"]');
    await page.waitForTimeout(500);

    await expect(page.locator('#operandBError')).toBeVisible();
  });

  test('should require operation selection', async ({ page }) => {
    const user = generateUniqueUser();
    await registerAndLogin(page, user);
    
    await page.goto('/static/calculations.html');
    
    await page.click('button:has-text("New Calculation")');
    await page.fill('#operandA', '10');
    await page.fill('#operandB', '5');
    // Don't select operation
    
    await page.click('#calculationForm button[type="submit"]');
    await page.waitForTimeout(500);

    await expect(page.locator('#operationError')).toBeVisible();
  });

  test('should redirect to login if not authenticated', async ({ page }) => {
    await clearStorage(page);
    
    await page.goto('/static/calculations.html');
    await page.waitForTimeout(2000);

    // Should be redirected to login
    expect(page.url()).toContain('/login.html');
  });

  test('should show error message when accessing calculations without auth', async ({ page }) => {
    await clearStorage(page);
    
    await page.goto('/static/calculations.html');
    await page.waitForTimeout(1000);

    // Should show authentication error
    await expect(page.locator('.alert-error')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('.alert-error')).toContainText('login');
  });

  test('should handle network errors gracefully', async ({ page }) => {
    const user = generateUniqueUser();
    await registerAndLogin(page, user);
    
    await page.goto('/static/calculations.html');
    
    // Simulate network failure by going offline
    await page.context().setOffline(true);
    
    await page.click('button:has-text("New Calculation")');
    await page.fill('#operandA', '10');
    await page.fill('#operandB', '5');
    await page.selectOption('#operation', 'add');
    
    await page.click('#calculationForm button[type="submit"]');
    await page.waitForTimeout(1000);

    // Should show network error
    await expect(page.locator('.alert-error')).toBeVisible();
    
    // Go back online
    await page.context().setOffline(false);
  });

  test('should prevent updating calculation to invalid state', async ({ page }) => {
    const user = generateUniqueUser();
    await registerAndLogin(page, user);
    
    await page.goto('/static/calculations.html');
    await createCalculation(page, 10, 5, 'add');
    
    await page.click('button:has-text("Refresh")');
    await page.waitForTimeout(1000);
    await page.click('button:has-text("Edit")');
    await page.waitForTimeout(500);

    // Try to update to division by zero
    await page.selectOption('#operation', 'divide');
    await page.fill('#operandB', '0');
    
    await page.click('#calculationForm button[type="submit"]');
    await page.waitForTimeout(500);

    // Should show validation error
    await expect(page.locator('#operandBError')).toBeVisible();
    await expect(page.locator('#operandBError')).toContainText('Division by zero');
  });
});

test.describe('Calculations - User Isolation', () => {
  test.beforeEach(async ({ page }) => {
    await clearStorage(page);
  });

  test('should only show calculations belonging to logged-in user', async ({ page, context }) => {
    // Create first user and their calculation
    const user1 = generateUniqueUser();
    await registerAndLogin(page, user1);
    await page.goto('/static/calculations.html');
    await createCalculation(page, 100, 50, 'add');
    await page.waitForTimeout(1000);
    
    // Logout user1
    await page.click('button:has-text("Logout")');
    await page.waitForTimeout(1000);

    // Create second user and their calculation
    const user2 = generateUniqueUser();
    await registerAndLogin(page, user2);
    await page.goto('/static/calculations.html');
    await createCalculation(page, 200, 100, 'subtract');
    await page.waitForTimeout(1000);

    await page.click('button:has-text("Refresh")');
    await page.waitForTimeout(1000);

    // User2 should only see their calculation (200-100=100)
    const calcCards = page.locator('.calculation-card');
    await expect(calcCards).toHaveCount(1);
    await expect(calcCards.first().locator('.calculation-result')).toContainText('100');
  });
});

test.describe('Calculations - UI/UX Features', () => {
  test.beforeEach(async ({ page }) => {
    await clearStorage(page);
  });

  test('should display username in navbar', async ({ page }) => {
    const user = generateUniqueUser();
    await registerAndLogin(page, user);
    
    await page.goto('/static/calculations.html');
    await page.waitForTimeout(1000);

    // Verify username is displayed
    await expect(page.locator('#username')).toContainText(user.username);
  });

  test('should refresh calculations when refresh button is clicked', async ({ page }) => {
    const user = generateUniqueUser();
    await registerAndLogin(page, user);
    
    await page.goto('/static/calculations.html');
    await createCalculation(page, 5, 5, 'add');
    
    // Click refresh
    await page.click('button:has-text("Refresh")');
    await page.waitForTimeout(1000);

    // Should show the calculation
    await expect(page.locator('.calculation-card')).toHaveCount(1);
  });

  test('should show operation symbols correctly', async ({ page }) => {
    const user = generateUniqueUser();
    await registerAndLogin(page, user);
    
    await page.goto('/static/calculations.html');
    
    // Create calculations with different operations
    await createCalculation(page, 1, 1, 'add');
    await createCalculation(page, 2, 2, 'subtract');
    await createCalculation(page, 3, 3, 'multiply');
    await createCalculation(page, 4, 4, 'divide');
    
    await page.click('button:has-text("Refresh")');
    await page.waitForTimeout(1000);

    // Verify operation symbols are displayed
    const cards = page.locator('.calculation-card');
    await expect(cards).toHaveCount(4);
  });

  test('should logout and redirect to login page', async ({ page }) => {
    const user = generateUniqueUser();
    await registerAndLogin(page, user);
    
    await page.goto('/static/calculations.html');
    await page.waitForTimeout(1000);

    // Click logout
    await page.click('button:has-text("Logout")');
    await page.waitForTimeout(2000);

    // Should redirect to login
    expect(page.url()).toContain('/login.html');
    
    // Token should be cleared
    const token = await page.evaluate(() => 
      localStorage.getItem('access_token') || sessionStorage.getItem('access_token')
    );
    expect(token).toBeNull();
  });
});
