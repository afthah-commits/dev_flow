with open('frontend/src/hooks/useAuth.tsx', 'r') as f:
    c = f.read()

c = c.replace('interface AuthContextType {\n  user: User | null;', 'interface AuthContextType {\n  user: User | null;\n  token: string | null;')
c = c.replace('export function AuthProvider({ children }: { children: React.ReactNode }) {\n  const [user, setUser] = useState<User | null>(null);', 'export function AuthProvider({ children }: { children: React.ReactNode }) {\n  const [user, setUser] = useState<User | null>(null);\n  const token = localStorage.getItem("token");')
c = c.replace('value={{ user, isAuthenticated: !!user, isLoading, login, logout }}', 'value={{ user, isAuthenticated: !!user, isLoading, login, logout, token }}')

with open('frontend/src/hooks/useAuth.tsx', 'w') as f:
    f.write(c)
