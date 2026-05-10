import fitz
from pathlib import Path

pdf_path = Path(r"E:/kcshji/project/openclaw/.openclaw/workspace/afsimpdf/AFSIM2.9参考手册-v1.1.pdf")
start_page = 1742
end_page = 1764
out_file = Path(r"e:/kcshji/project/openclaw/.openclaw/workspace/skills/afsim-project/references/extracted_1742_1764.txt")
img_dir = Path(r"e:/kcshji/project/openclaw/.openclaw/workspace/skills/afsim-project/references/extracted_images_1742_1764")
img_dir.mkdir(parents=True, exist_ok=True)

with fitz.open(pdf_path) as doc, out_file.open('w', encoding='utf-8') as outf:
    for pno in range(start_page-1, end_page):
        page = doc.load_page(pno)
        text = page.get_text('text')
        outf.write(f"=== Page {pno+1} ===\n")
        if text.strip():
            outf.write(text + '\n')
        # extract images
        for img_index, img in enumerate(page.get_images(full=True), start=1):
            xref = img[0]
            base_image = doc.extract_image(xref)
            img_bytes = base_image['image']
            ext = base_image.get('ext', 'png')
            img_name = img_dir / f'page{pno+1}_img{img_index}.{ext}'
            with open(img_name, 'wb') as imf:
                imf.write(img_bytes)
            outf.write(f'[IMAGE: {img_name}]\n')
        outf.write('\n')

print('Extraction complete ->', out_file)
