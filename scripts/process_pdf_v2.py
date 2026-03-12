
import re
import os

input_path = r'c:\Users\javen\OneDrive\Desktop\AgentAIMO\temp_raw_imo_bench.txt'
output_base = r'c:\Users\javen\OneDrive\Desktop\AgentAIMO\2511.01846v1_Part'

def latexify_basic(text):
    # Basic math replacements using simple string replace for safety
    # First, handle simple symbols
    simple_replacements = [
        ('!=', r'$\neq$'),
        ('<=', r'$\le$'),
        ('>=', r'$\ge$'),
        ('~', r'$\sim$'),
        ('×', r'$\times$'),
        ('⋄', '*'), 
        ('†', '^t'),
    ]
    for old, new in simple_replacements:
        text = text.replace(old, new)

    # Regex replacements for dynamic patterns
    # x^y -> $x^y$
    text = re.sub(r'(\d+)\^(\d+)', lambda m: f"${m.group(1)}^{{{m.group(2)}}}$", text)
    # x_y -> $x_y$ (basic alpha_alpha)
    text = re.sub(r'(\b[A-Za-z]+)_(\w+)', lambda m: f"${m.group(1)}_{{{m.group(2)}}}$", text)
        
    return text

def clean_lines(text):
    # Remove markers
    text = text.replace('==Start of PDF==', '')
    text = re.sub(r'==Screenshot for page \d+==', '', text)
    text = text.replace('==End of PDF==', '')
    return text

def normalize_whitespace(text):
    # Remove excessive whitespace:
    # 1. Replace multiple newlines with a single newline (or two for paragraphs).
    # 2. Replace multiple spaces/tabs with single space.
    # The user wants "dense" but "coherent".
    # Let's reduce consecutive whitespace to single space, EXCEPT newlines which denote structure.
    
    # Strategy: Split by newlines, clean each line, join by single newline?
    # Or join by space if it's a wrapped line? 
    # PDF text often has hard wraps. Joining by space is usually better for "dense text".
    # But headers should stay separate.
    
    # We will handle density *after* section extraction to preserve headers.
    return text.strip()

def main():
    if not os.path.exists(input_path):
        print(f"Input file not found: {input_path}")
        return

    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    content = clean_lines(content)
    
    # Identify Sections
    # Headers like "1. Introduction", "A. IMO-AnswerBench", "References"
    # We look for lines starting with these patterns.
    
    lines = content.splitlines()
    sections = []
    current_section_title = "Preamble"
    current_section_lines = []
    
    # Regex for headers:
    # Start of line, (Digit+ dot or Letter dot), Space, Text
    # Or specific words "References", "Acknowledgments"
    header_pattern = re.compile(r'^(\d+\.|[A-Z]\.)\s+.*|^(References|Acknowledgments|Conclusion)$')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if header_pattern.match(line):
            # Finish previous section
            if current_section_lines:
                # Process the previous section text
                # Join with space to densify (reflow paragraphs)
                full_text = " ".join(current_section_lines)
                full_text = latexify_basic(full_text)
                sections.append(f"\n\n### {current_section_title}\n{full_text}")
            
            # Start new section
            current_section_title = line
            current_section_lines = []
        else:
            current_section_lines.append(line)
            
    # Flush last section
    if current_section_lines:
        full_text = " ".join(current_section_lines)
        full_text = latexify_basic(full_text)
        sections.append(f"\n\n### {current_section_title}\n{full_text}")

    # Now bundle sections into chunks
    # User constraint: "no chunk with an incomplete section"
    # We concatenate sections until size limit is hit.
    
    chunk_limit = 80000 
    chunks = []
    current_chunk = ""
    
    for section_text in sections:
        if len(current_chunk) + len(section_text) > chunk_limit:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = section_text
        else:
            current_chunk += section_text
            
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    print(f"Split into {len(chunks)} parts.")
    
    for i, chunk in enumerate(chunks):
        out_name = f"{output_base}{i+1}.txt"
        with open(out_name, 'w', encoding='utf-8') as f:
            f.write(chunk)
        print(f"Created {out_name} ({len(chunk)} chars)")

if __name__ == "__main__":
    main()
