# Front-End Authentication Pages

## Overview

This project includes two complete front-end authentication pages with client-side validation, JWT token management, and modern UI design.

## Pages

### 1. Register Page - `register.html`

**Location:** `/static/register.html`

**URL:** `http://localhost:8000/static/register.html`

#### Features

✅ **Form Fields:**
- Username (3-50 characters, required)
- Email (valid email format, required)
- Password (minimum 8 characters, required)
- Confirm Password (must match password, required)

✅ **Client-Side Validation:**
- Email format validation using regex
- Username length validation (3-50 characters)
- Password minimum length (8 characters)
- Password strength indicator (weak/medium/strong)
- Password match confirmation
- Real-time validation as user types
- Visual feedback (error/success states)

✅ **Password Strength Indicator:**
- **Weak:** Basic password (< 8 chars or simple)
- **Medium:** Good password (8+ chars with some complexity)
- **Strong:** Excellent password (12+ chars with mixed case, numbers, special chars)

✅ **On Success (201 Created):**
- Displays success message
- Stores JWT token in `localStorage`
- Stores user information in `localStorage`
- Redirects to home page after 1.5 seconds
- Logs authentication info to console

✅ **Error Handling:**
- 400 Bad Request: Username/email already exists
- 422 Validation Error: Invalid input format
- Network errors with user-friendly messages
- Field-specific error messages

#### Form Validation Rules

```javascript
// Email validation
/^[^\s@]+@[^\s@]+\.[^\s@]+$/

// Username validation
3 <= length <= 50

// Password validation
length >= 8

// Password strength calculation
- 8+ characters
- 12+ characters (bonus)
- Mixed case letters
- Contains numbers
- Contains special characters
```

---

### 2. Login Page - `login.html`

**Location:** `/static/login.html`

**URL:** `http://localhost:8000/static/login.html`

#### Features

✅ **Form Fields:**
- Username or Email (accepts both, required)
- Password (required)
- Remember Me checkbox (optional)

✅ **Client-Side Validation:**
- Non-empty username/email field
- Non-empty password field
- Basic validation (minimal as requested)
- Visual feedback on input

✅ **Remember Me Functionality:**
- **Checked:** Stores token in `localStorage` (persists across sessions)
- **Unchecked:** Stores token in `sessionStorage` (cleared when browser closes)

✅ **On Success (200 OK):**
- Displays success message
- Stores JWT token (localStorage or sessionStorage based on "Remember Me")
- Stores user information
- Redirects to home page after 1 second
- Logs authentication info to console

✅ **Error Handling:**
- 401 Unauthorized: Invalid credentials
- 403 Forbidden: Account inactive
- Network errors with user-friendly messages
- Clears password field on failed login

✅ **Additional Features:**
- Forgot password link (placeholder)
- Automatic redirect if already logged in
- Navigation link to registration page

---

## Authentication Utilities - `auth.js`

**Location:** `/static/auth.js`

A shared JavaScript library for managing authentication across all pages.

### Available Functions

```javascript
// Get JWT token from storage
getToken()

// Get token type (e.g., "bearer")
getTokenType()

// Get stored user information
getUser()

// Check if user is authenticated
isAuthenticated()

// Logout user (clear all tokens)
logout()

// Make authenticated API requests
authenticatedFetch(url, options)

// Decode JWT token payload
decodeToken(token)

// Check if token is expired
isTokenExpired(token)

// Validate current session
validateSession()

// Require authentication (redirect if not logged in)
requireAuth(redirectUrl)
```

### Usage Examples

```javascript
// Include auth.js in your HTML
<script src="/static/auth.js"></script>

// Check if user is logged in
if (isAuthenticated()) {
    const user = getUser();
    console.log('Welcome,', user.username);
}

// Make authenticated API call
try {
    const response = await authenticatedFetch('/users/me');
    const userData = await response.json();
    console.log(userData);
} catch (error) {
    console.error('Request failed:', error);
}

// Logout
document.getElementById('logoutBtn').addEventListener('click', () => {
    logout();
    window.location.href = '/static/login.html';
});

// Protect a page (require login)
requireAuth(); // Redirects to login if not authenticated
```

---

## Stored Data Structure

### LocalStorage/SessionStorage

When a user successfully registers or logs in, the following data is stored:

```javascript
// JWT Access Token
localStorage.setItem('access_token', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...')

// Token Type
localStorage.setItem('token_type', 'bearer')

// User Information
localStorage.setItem('user', JSON.stringify({
    "id": 1,
    "username": "johndoe",
    "email": "john.doe@example.com",
    "created_at": "2025-12-04T12:00:00",
    "updated_at": "2025-12-04T12:00:00",
    "is_active": true
}))
```

### Storage Types

- **localStorage:** Persists even after browser closes (used with "Remember Me")
- **sessionStorage:** Cleared when browser tab/window closes (default for login)

---

## UI/UX Features

### Design

- **Modern gradient background** (purple to violet)
- **Clean white card** with rounded corners
- **Smooth animations** for alerts and interactions
- **Responsive design** works on mobile and desktop
- **Consistent styling** across both pages

### Visual Feedback

- **Input States:**
  - Default: Gray border
  - Focus: Blue border with subtle shadow
  - Error: Red border with error message
  - Success: Green border

- **Loading States:**
  - Button disabled during submission
  - Spinning loader animation
  - Button text hidden while loading

- **Alerts:**
  - Success: Green background
  - Error: Red background
  - Info: Blue background
  - Auto-dismiss after 5 seconds (success only)

### Accessibility

- Proper form labels
- Semantic HTML
- Keyboard navigation support
- Clear error messages
- ARIA-friendly structure

---

## Testing the Pages

### Manual Testing

1. **Start the application:**
   ```bash
   docker-compose up
   ```

2. **Test Registration:**
   - Navigate to: `http://localhost:8000/static/register.html`
   - Try invalid inputs (watch validation)
   - Submit with valid data
   - Check browser console for JWT token
   - Check localStorage/sessionStorage

3. **Test Login:**
   - Navigate to: `http://localhost:8000/static/login.html`
   - Try invalid credentials (should get 401)
   - Login with valid credentials
   - Test "Remember Me" functionality
   - Check token storage location

4. **Test Already Logged In:**
   - While logged in, visit register or login page
   - Should see "already logged in" message
   - Should redirect to home

### Validation Testing

**Register Page:**
```javascript
// Test cases
✓ Username < 3 chars → Error
✓ Username > 50 chars → Error
✓ Invalid email format → Error
✓ Password < 8 chars → Error
✓ Passwords don't match → Error
✓ Duplicate username → 400 error from server
✓ Duplicate email → 400 error from server
✓ Valid data → 201 success with JWT
```

**Login Page:**
```javascript
// Test cases
✓ Empty username → Error
✓ Empty password → Error
✓ Invalid credentials → 401 error
✓ Valid credentials → 200 success with JWT
✓ Remember me checked → localStorage
✓ Remember me unchecked → sessionStorage
```

---

## Integration with Backend

### API Endpoints Used

**Register:**
```http
POST /users/register
Content-Type: application/json

{
  "username": "johndoe",
  "email": "john.doe@example.com",
  "password": "securepassword123"
}
```

**Login:**
```http
POST /users/login
Content-Type: application/json

{
  "username": "johndoe",
  "password": "securepassword123"
}
```

### Expected Responses

**Success Response (Register/Login):**
```json
{
  "message": "Registration successful" | "Login successful",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john.doe@example.com",
    "created_at": "2025-12-04T12:00:00",
    "updated_at": "2025-12-04T12:00:00",
    "is_active": true
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses:**
```json
// 400 Bad Request
{
  "detail": "Username already registered"
}

// 401 Unauthorized
{
  "detail": "Invalid username or password"
}

// 422 Validation Error
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

---

## Customization

### Change Redirect Target

After successful login/register, users are redirected to `/`. To change this:

```javascript
// In register.html and login.html
setTimeout(() => {
    window.location.href = '/dashboard';  // Change this URL
}, 1500);
```

### Modify Validation Rules

```javascript
// In register.html
function validatePassword(password) {
    return password.length >= 12;  // Change minimum length
}
```

### Update Styling

Both pages use embedded CSS. Key color variables:

```css
/* Gradient background */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Primary color (buttons, links) */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
color: #667eea;

/* Success color */
color: #27ae60;

/* Error color */
color: #e74c3c;
```

---

## Browser Compatibility

- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Mobile browsers

**Requirements:**
- ES6+ JavaScript support
- Fetch API support
- LocalStorage/SessionStorage support

---

## Security Considerations

✅ **Implemented:**
- HTTPS recommended for production
- Tokens stored in browser storage (not cookies to avoid CSRF)
- Password not logged or stored in plain text
- Client-side validation (backend validation is primary)
- Auto-redirect if already authenticated

⚠️ **Recommendations:**
- Use HTTPS in production
- Implement token refresh mechanism
- Add CSRF protection if using cookies
- Implement rate limiting on backend
- Add password reset functionality
- Consider implementing 2FA

---

## Files Created

1. `static/register.html` - Registration page
2. `static/login.html` - Login page  
3. `static/auth.js` - Authentication utilities
4. `docs/FRONTEND_AUTHENTICATION.md` - This documentation

---

## Next Steps

1. ✅ Pages are ready to use
2. Start the application: `docker-compose up`
3. Visit `http://localhost:8000/static/register.html`
4. Create an account and test the flow
5. Customize redirect URLs and styling as needed
6. Consider adding protected pages using `auth.js`
