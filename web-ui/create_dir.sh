# Navigate to your client directory
cd client

# Create the new directories
mkdir -p src/components/auth
mkdir -p src/contexts
mkdir -p src/pages/auth
mkdir -p src/types

# Create the individual files (you can copy the content from above)
touch src/types/auth.ts
touch src/types/index.ts

touch src/contexts/AuthContext.tsx
touch src/contexts/index.ts

touch src/components/auth/LoginForm.tsx
touch src/components/auth/RegisterForm.tsx
touch src/components/auth/ForgotPasswordForm.tsx
touch src/components/auth/ProtectedRoute.tsx
touch src/components/auth/PublicRoute.tsx
touch src/components/auth/index.ts

touch src/pages/auth/LoginPage.tsx
touch src/pages/auth/RegisterPage.tsx
touch src/pages/auth/ForgotPasswordPage.tsx
touch src/pages/auth/index.ts

# Update main pages index if it doesn't exist
touch src/pages/index.ts