import zipfile
import re
import json
import os

def parse_epub_to_chapters():
    epub_path = r"d:\NIdan_bot\knowledgebase\madhavnidan\Ayurvedic Diagnostics Madhava Nidana Of Madhavakara Vol 1 Ed With Notes By Brahmanand Tripathi Trans By Kanjiv Lochan Varanasi - Chaukhamba Surbharati Prakashan.epub"
    
    if not os.path.exists(epub_path):
        print(f"Error: EPUB file not found at {epub_path}")
        return
        
    print("Parsing EPUB file...")
    with zipfile.ZipFile(epub_path, 'r') as zip_ref:
        namelist = zip_ref.namelist()
        pages = [name for name in namelist if name.startswith("EPUB/page_") and name.endswith(".html")]
        # Sort pages numerically
        pages.sort(key=lambda x: int(re.search(r'\d+', x).group()))
        
        # We will parse all pages and extract their text
        full_text_by_page = {}
        for page in pages:
            page_num = int(re.search(r'\d+', page).group())
            content = zip_ref.read(page).decode('utf-8', errors='ignore')
            # Strip HTML tags
            text = re.sub(r'<[^>]+>', ' ', content)
            # Normalize whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            full_text_by_page[page_num] = text
            
    # Now let's define chapter boundaries based on page analysis
    # We will map page ranges to chapters
    chapter_definitions = [
        {"num": 1, "title": "Pancha Nidana Laksanam", "start_page": 42, "end_page": 109, "type": "Nidana"},
        {"num": 2, "title": "Jvara Nidanam", "start_page": 110, "end_page": 191, "type": "Nidana"},
        {"num": 3, "title": "Atisara Nidanam", "start_page": 192, "end_page": 215, "type": "Nidana"},
        {"num": 4, "title": "Grahani Roga Nidanam", "start_page": 216, "end_page": 227, "type": "Nidana"},
        {"num": 5, "title": "Arsa Nidanam", "start_page": 228, "end_page": 252, "type": "Nidana"},
        {"num": 6, "title": "Agnimandya Ajirna Visucika Alasaka Vilambika Nidanam", "start_page": 253, "end_page": 271, "type": "Nidana"},
        {"num": 7, "title": "Krmi Nidanam", "start_page": 272, "end_page": 278, "type": "Nidana"},
        {"num": 8, "title": "Panduroga Kamala Kumbha-Kamala Halimaka Nidanam", "start_page": 279, "end_page": 296, "type": "Nidana"},
        {"num": 9, "title": "Raktapitta Nidanam", "start_page": 297, "end_page": 307, "type": "Nidana"},
        {"num": 10, "title": "Rajayaksma Ksataksina Nidanam", "start_page": 308, "end_page": 326, "type": "Nidana"},
        {"num": 11, "title": "Kasa Nidanam", "start_page": 327, "end_page": 338, "type": "Nidana"},
        {"num": 12, "title": "Hikka Svasa Nidanam", "start_page": 339, "end_page": 358, "type": "Nidana"},
        {"num": 13, "title": "Svarabheda Nidanam", "start_page": 359, "end_page": 364, "type": "Nidana"},
        {"num": 14, "title": "Arocaka Nidanam", "start_page": 365, "end_page": 370, "type": "Nidana"},
        {"num": 15, "title": "Chardi Nidanam", "start_page": 371, "end_page": 378, "type": "Nidana"},
        {"num": 16, "title": "Trsna Nidanam", "start_page": 379, "end_page": 387, "type": "Nidana"},
        {"num": 17, "title": "Murcha Bhrama Nidra Tandra Samnyasa Nidanam", "start_page": 388, "end_page": 401, "type": "Nidana"},
        {"num": 18, "title": "Panatyaya Paramada Panajirana Panavibhrama Nidanam", "start_page": 402, "end_page": 415, "type": "Nidana"},
        {"num": 19, "title": "Daha Nidanam", "start_page": 416, "end_page": 421, "type": "Nidana"},
        {"num": 20, "title": "Unmada Nidanam", "start_page": 422, "end_page": 442, "type": "Nidana"},
        {"num": 21, "title": "Apasmara Nidanam", "start_page": 443, "end_page": 449, "type": "Nidana"},
        {"num": 22, "title": "Vatavyadhi Nidanam", "start_page": 450, "end_page": 493, "type": "Nidana"},
        {"num": 23, "title": "Vatarakta Nidanam", "start_page": 494, "end_page": 502, "type": "Nidana"},
        {"num": 24, "title": "Urustambha Nidanam", "start_page": 503, "end_page": 507, "type": "Nidana"},
        {"num": 25, "title": "Amavata Nidanam", "start_page": 508, "end_page": 514, "type": "Nidana"},
        {"num": 26, "title": "Sula Parinamasula Annadravasula Nidanam", "start_page": 515, "end_page": 527, "type": "Nidana"},
        {"num": 27, "title": "Udavartadi Nidanam", "start_page": 528, "end_page": 534, "type": "Nidana"},
        {"num": 28, "title": "Gulma Nidanam", "start_page": 535, "end_page": 547, "type": "Nidana"},
        {"num": 29, "title": "Hrdroga Nidanam", "start_page": 548, "end_page": 554, "type": "Nidana"},
        {"num": 30, "title": "Mutrakrcchra Nidanam", "start_page": 555, "end_page": 559, "type": "Nidana"},
        {"num": 31, "title": "Mutraghata Nidanam", "start_page": 560, "end_page": 571, "type": "Nidana"},
        {"num": 32, "title": "Asmari Nidanam", "start_page": 572, "end_page": 588, "type": "Nidana"}
    ]
    
    structured_chapters = []
    for ch in chapter_definitions:
        ch_text_parts = []
        for p_num in range(ch["start_page"], ch["end_page"] + 1):
            if p_num in full_text_by_page:
                ch_text_parts.append(full_text_by_page[p_num])
        
        ch_content = "\n".join(ch_text_parts)
        structured_chapters.append({
            "book_name": "Madhava Nidana",
            "section_name": "Volume 1",
            "chapter_number": ch["num"],
            "chapter_title": ch["title"],
            "chapter_type": ch["type"],
            "start_page": ch["start_page"],
            "end_page": ch["end_page"],
            "content": ch_content
        })
        
    os.makedirs(r"d:\NIdan_bot\backend\data", exist_ok=True)
    raw_chapters_path = r"d:\NIdan_bot\backend\data\raw_chapters.json"
    with open(raw_chapters_path, 'w', encoding='utf-8') as f:
        json.dump(structured_chapters, f, ensure_ascii=False, indent=2)
        
    print(f"Saved {len(structured_chapters)} chapters to {raw_chapters_path}")

if __name__ == "__main__":
    parse_epub_to_chapters()
