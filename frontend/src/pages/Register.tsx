import React, { useState, useEffect } from "react";
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
        <label htmlFor="name" className="block text-sm font-medium text-gray-300 mb-1">Name</label>
        <Input id="name" required value={name} onChange={e => setName(e.target.value)} />
      </div>

      <div>
        <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-1">Email address</label>
        <Input id="email" type="email" required value={email} onChange={e => setEmail(e.target.value)} />
      </div>

      <div>
        <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-1">Password</label>
        <Input id="password" type="password" required minLength={8} value={password} onChange={e => setPassword(e.target.value)} />
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
