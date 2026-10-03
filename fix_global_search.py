with open('frontend/src/components/GlobalSearch.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

replacement = '''
              {!loading && results.projects.length === 0 && results.tasks.length === 0 && results.discussions.length === 0 && (
                <div className="p-4 text-center text-gray-500">No results found for "{query}"</div>
              )}
'''

new_commands = '''
              {!loading && results.projects.length === 0 && results.tasks.length === 0 && results.discussions.length === 0 && (
                <div className="p-4 text-center text-gray-500">No results found for "{query}"</div>
              )}
            </div>
          )}
          
          {!results && !loading && (
            <div className="p-4 space-y-2">
              <div className="px-3 py-1 text-xs font-semibold text-gray-500 uppercase">Commands</div>
              <button onClick={() => { navigate('/projects/new'); setIsOpen(false); }} className="w-full text-left px-3 py-2 hover:bg-gray-800 rounded text-gray-300">Create Project</button>
              <button onClick={() => { navigate('/projects'); setIsOpen(false); }} className="w-full text-left px-3 py-2 hover:bg-gray-800 rounded text-gray-300">Open Projects</button>
              <button onClick={() => { navigate('/analytics/collaboration'); setIsOpen(false); }} className="w-full text-left px-3 py-2 hover:bg-gray-800 rounded text-gray-300">Open Analytics</button>
              <button onClick={() => { navigate('/settings/notifications'); setIsOpen(false); }} className="w-full text-left px-3 py-2 hover:bg-gray-800 rounded text-gray-300">Open Notifications</button>
            </div>
          )}
'''

# Replace the "Type to start searching globally" with commands
target2 = '''
          {!results && !loading && (
            <div className="p-8 text-center text-gray-600 flex flex-col items-center gap-2">
              <Search className="w-8 h-8 opacity-20" />
              <p>Type to start searching globally</p>
            </div>
          )}
'''

content = content.replace(target2, "")
content = content.replace(replacement, new_commands)

with open('frontend/src/components/GlobalSearch.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
