from bs4 import BeautifulSoup

html_content = "<html><head><style>body {font-family: Arial;}</style></head><body><h1>Hello, World!</h1><p>This is a paragraph.</p><script>alert('Hi');</script></body></html>"

soup = BeautifulSoup(html_content, 'lxml')

# Remove style and script tags
for tag in soup(["script", "style"]):
    tag.decompose()

text = soup.get_text()
print(text.strip())