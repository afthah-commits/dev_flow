with open('frontend/src/hooks/useAuth.tsx', 'r') as f:
    c = f.read()

c = c.replace('interface AuthContextType {\n  user: User | null;', 'interface AuthContextType {\n  user: User | null;\n  currentOrganization?: { id: string };\n  token?: string;')
c = c.replace('export function AuthProvider({ children }: { children: React.ReactNode }) {\n  const [user, setUser] = useState<User | null>(null);', 'export function AuthProvider({ children }: { children: React.ReactNode }) {\n  const [user, setUser] = useState<User | null>(null);\n  const currentOrganization = { id: "default-org" };\n  const token = localStorage.getItem("token") || "";')
c = c.replace('return (\n    <AuthContext.Provider', 'return (\n    <AuthContext.Provider\n      value={{ user, isAuthenticated: !!user, isLoading, login, logout, currentOrganization, token }}')

# the original value={{ user, isAuthenticated: !!user, isLoading, login, logout }}
import re
c = re.sub(r'value={{ user, isAuthenticated: !!user, isLoading, login, logout }}', r'', c)

with open('frontend/src/hooks/useAuth.tsx', 'w') as f:
    f.write(c)
