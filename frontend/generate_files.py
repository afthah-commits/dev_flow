import os

base_dir = "c:/personal_projects/devflow/frontend"
dirs = [
    "src/components/ui",
    "src/features/auth",
    "src/hooks",
    "src/layouts",
    "src/lib",
    "src/pages",
    "src/routes",
    "src/types",
]

for d in dirs:
    os.makedirs(os.path.join(base_dir, d), exist_ok=True)

files = {}

files["src/lib/utils.ts"] = """import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
"""

files["src/lib/axios.ts"] = """import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
"""

files["src/types/index.ts"] = """export interface User {
  id: string;
  name: string;
  email: string;
  avatar_url?: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
  last_login_at?: string;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
"""

files["src/hooks/useAuth.tsx"] = """import React, { createContext, useContext, useEffect, useState } from "react";
import { User } from "../types";
import { api } from "../lib/axios";

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (token: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem("token");
      if (token) {
        try {
          const res = await api.get("/auth/me");
          setUser(res.data);
        } catch (error) {
          localStorage.removeItem("token");
        }
      }
      setIsLoading(false);
    };
    initAuth();
  }, []);

  const login = async (token: string) => {
    localStorage.setItem("token", token);
    const res = await api.get("/auth/me");
    setUser(res.data);
  };

  const logout = () => {
    localStorage.removeItem("token");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
"""

files["src/components/ui/Button.tsx"] = """import React from "react";
import { cn } from "../../lib/utils";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline";
  isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", isLoading, children, ...props }, ref) => {
    const baseStyles = "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 disabled:pointer-events-none disabled:opacity-50 h-10 px-4 py-2";
    const variants = {
      primary: "bg-blue-600 text-white hover:bg-blue-700",
      secondary: "bg-gray-800 text-gray-50 hover:bg-gray-700",
      outline: "border border-gray-600 text-gray-200 hover:bg-gray-800",
    };
    
    return (
      <button
        ref={ref}
        className={cn(baseStyles, variants[variant], className)}
        disabled={isLoading || props.disabled}
        {...props}
      >
        {isLoading && <span className="mr-2 animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>}
        {children}
      </button>
    );
  }
);
Button.displayName = "Button";
"""

files["src/components/ui/Input.tsx"] = """import React from "react";
import { cn } from "../../lib/utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, error, ...props }, ref) => {
    return (
      <div className="flex flex-col space-y-1 w-full">
        <input
          ref={ref}
          className={cn(
            "flex h-10 w-full rounded-md border border-gray-600 bg-gray-900 px-3 py-2 text-sm text-gray-100 placeholder:text-gray-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 disabled:cursor-not-allowed disabled:opacity-50",
            error && "border-red-500 focus-visible:ring-red-500",
            className
          )}
          {...props}
        />
        {error && <span className="text-xs text-red-500">{error}</span>}
      </div>
    );
  }
);
Input.displayName = "Input";
"""

files["src/layouts/AuthLayout.tsx"] = """import React from "react";
import { Outlet, Navigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function AuthLayout() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <div className="min-h-screen bg-gray-950 flex items-center justify-center text-gray-200">Loading...</div>;
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 text-gray-100">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="mt-6 text-center text-3xl font-bold tracking-tight text-white">
          DevFlow
        </h2>
      </div>
      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-gray-900 py-8 px-4 shadow sm:rounded-lg sm:px-10 border border-gray-800">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
"""

files["src/layouts/DashboardLayout.tsx"] = """import React from "react";
import { Outlet, Navigate, Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export default function DashboardLayout() {
  const { user, isAuthenticated, isLoading, logout } = useAuth();

  if (isLoading) {
    return <div className="min-h-screen bg-gray-950 flex items-center justify-center text-gray-200">Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col text-gray-100">
      <nav className="border-b border-gray-800 bg-gray-900 px-6 py-4 flex items-center justify-between">
        <div className="text-xl font-bold text-white">DevFlow</div>
        <div className="flex items-center space-x-6">
          <Link to="/" className="hover:text-white transition-colors">Dashboard</Link>
          <Link to="/profile" className="hover:text-white transition-colors">Profile</Link>
          <div className="flex items-center space-x-3 ml-4 border-l border-gray-700 pl-4">
            <span className="text-sm">{user?.name}</span>
            <button onClick={logout} className="text-sm text-gray-400 hover:text-white">Logout</button>
          </div>
        </div>
      </nav>
      <main className="flex-1 p-6">
        <Outlet />
      </main>
    </div>
  );
}
"""

files["src/pages/Login.tsx"] = """import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { api } from "../lib/axios";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);
    try {
      const res = await api.post("/auth/login", { email, password });
      await login(res.data.access_token);
      navigate("/");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to login. Check your credentials.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form className="space-y-6" onSubmit={handleSubmit}>
      <h3 className="text-xl font-medium text-white mb-6">Sign in to your account</h3>
      {error && <div className="p-3 text-sm text-red-500 bg-red-950/50 border border-red-900 rounded-md">{error}</div>}
      
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-1">Email address</label>
        <Input type="email" required value={email} onChange={e => setEmail(e.target.value)} />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-300 mb-1">Password</label>
        <Input type="password" required value={password} onChange={e => setPassword(e.target.value)} />
      </div>

      <div className="flex items-center justify-between">
        <Link to="/forgot-password" className="text-sm text-blue-500 hover:text-blue-400">
          Forgot your password?
        </Link>
      </div>

      <Button type="submit" className="w-full" isLoading={isLoading}>
        Sign in
      </Button>
      
      <p className="text-center text-sm text-gray-400 mt-4">
        Don't have an account? <Link to="/register" className="text-blue-500 hover:text-blue-400">Sign up</Link>
      </p>
    </form>
  );
}
"""

files["src/pages/Register.tsx"] = """import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../lib/axios";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";

export default function Register() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);
    try {
      await api.post("/auth/register", { name, email, password });
      navigate("/login");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to register.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form className="space-y-6" onSubmit={handleSubmit}>
      <h3 className="text-xl font-medium text-white mb-6">Create an account</h3>
      {error && <div className="p-3 text-sm text-red-500 bg-red-950/50 border border-red-900 rounded-md">{error}</div>}
      
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-1">Name</label>
        <Input required value={name} onChange={e => setName(e.target.value)} />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-300 mb-1">Email address</label>
        <Input type="email" required value={email} onChange={e => setEmail(e.target.value)} />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-300 mb-1">Password</label>
        <Input type="password" required minLength={8} value={password} onChange={e => setPassword(e.target.value)} />
      </div>

      <Button type="submit" className="w-full" isLoading={isLoading}>
        Sign up
      </Button>
      
      <p className="text-center text-sm text-gray-400 mt-4">
        Already have an account? <Link to="/login" className="text-blue-500 hover:text-blue-400">Sign in</Link>
      </p>
    </form>
  );
}
"""

files["src/pages/ForgotPassword.tsx"] = """import React from "react";
import { Link } from "react-router-dom";

export default function ForgotPassword() {
  return (
    <div className="space-y-6">
      <h3 className="text-xl font-medium text-white mb-6">Reset Password</h3>
      <p className="text-gray-400 text-sm mb-4">Password reset is not implemented in Phase 1.</p>
      <Link to="/login" className="block text-center text-sm text-blue-500 hover:text-blue-400">
        Return to sign in
      </Link>
    </div>
  );
}
"""

files["src/pages/Dashboard.tsx"] = """import React from "react";

export default function Dashboard() {
  return (
    <div className="max-w-7xl mx-auto py-6">
      <h1 className="text-3xl font-bold text-white">Welcome to DevFlow</h1>
      <p className="mt-4 text-gray-400">This is Phase 1. Authentication and architecture setup is complete.</p>
    </div>
  );
}
"""

files["src/pages/Profile.tsx"] = """import React from "react";
import { useAuth } from "../hooks/useAuth";

export default function Profile() {
  const { user } = useAuth();
  
  return (
    <div className="max-w-3xl mx-auto py-6">
      <h1 className="text-3xl font-bold text-white mb-6">Profile</h1>
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
        <div className="space-y-4">
          <div>
            <label className="text-sm text-gray-400">Name</label>
            <div className="text-lg text-gray-100">{user?.name}</div>
          </div>
          <div>
            <label className="text-sm text-gray-400">Email</label>
            <div className="text-lg text-gray-100">{user?.email}</div>
          </div>
          <div>
            <label className="text-sm text-gray-400">Member since</label>
            <div className="text-lg text-gray-100">{user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'Unknown'}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
"""

files["src/App.tsx"] = """import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./hooks/useAuth";
import AuthLayout from "./layouts/AuthLayout";
import DashboardLayout from "./layouts/DashboardLayout";
import Login from "./pages/Login";
import Register from "./pages/Register";
import ForgotPassword from "./pages/ForgotPassword";
import Dashboard from "./pages/Dashboard";
import Profile from "./pages/Profile";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route element={<AuthLayout />}>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
          </Route>
          
          <Route element={<DashboardLayout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/profile" element={<Profile />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
"""

files["src/main.tsx"] = """import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
"""

files[".env"] = """VITE_API_URL=http://localhost:8000/api/v1
"""

files["Dockerfile"] = """FROM node:24-alpine

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
"""

for path, content in files.items():
    with open(os.path.join(base_dir, path), "w") as f:
        f.write(content)

print("Frontend files generated successfully.")
