with open('app/matcher.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace any escaped double quotes with unescaped ones
fixed_content = content.replace('\\"', '"')

with open('app/matcher.py', 'w', encoding='utf-8') as f:
    f.write(fixed_content)

print("matcher.py has been fixed!")
