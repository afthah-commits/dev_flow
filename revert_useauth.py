with open('frontend/src/hooks/useAuth.tsx', 'r') as f:
    c = f.read()

c = c.replace('  currentOrganization?: { id: string };\n  token?: string;', '')
c = c.replace('  const currentOrganization = { id: "default-org" };\n  const token = localStorage.getItem("token") || "";', '')
c = c.replace('value={{ user, isAuthenticated: !!user, isLoading, login, logout, currentOrganization, token }}', 'value={{ user, isAuthenticated: !!user, isLoading, login, logout }}')

with open('frontend/src/hooks/useAuth.tsx', 'w') as f:
    f.write(c)
