with open('frontend/src/components/GlobalSearch.tsx', 'r') as f:
    c = f.read()

c = c.replace("""          )}
            </div>
          )}
                  </div>
      </div>
    </div>
  );
}""", """          )}
        </div>
      </div>
    </div>
  );
}""")

with open('frontend/src/components/GlobalSearch.tsx', 'w') as f:
    f.write(c)
