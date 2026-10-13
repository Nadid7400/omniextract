import sys
import io
import os
import json
import time

sys.path.insert(0, r"c:\Users\NADID\Desktop\Anything extractor")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from backend.fb_extractor import FacebookExtractor, extract_all_facebook_urls

# Raw text with all 93 links from user's request
raw_user_text = """
1.[https://www.facebook.com/share/p/1DyLPPg1BQ/](https://www.facebook.com/share/p/1DyLPPg1BQ/) 2.[https://www.facebook.com/share/p/1JbBJtWm5F/](https://www.facebook.com/share/p/1JbBJtWm5F/) 3.[https://www.facebook.com/share/1Bn8sibqGp/](https://www.facebook.com/share/1Bn8sibqGp/) 4.[https://www.facebook.com/share/1XY9ZebCKk/](https://www.facebook.com/share/1XY9ZebCKk/) 5.[https://www.facebook.com/share/1LoF6peFGM/48.https://www.facebook.com/share/p/1CgDqdNJHd/](https://www.facebook.com/share/1LoF6peFGM/48.https://www.facebook.com/share/p/1CgDqdNJHd/) 6.[https://www.facebook.com/share/1EXr8FjNaR/](https://www.facebook.com/share/1EXr8FjNaR/) 7.[https://www.facebook.com/share/19QmHagXDy/](https://www.facebook.com/share/19QmHagXDy/) 8.[https://www.facebook.com/share/1DkdRYBNtL/](https://www.facebook.com/share/1DkdRYBNtL/) 9.[https://www.facebook.com/share/14pBSgE1ZDp/](https://www.facebook.com/share/14pBSgE1ZDp/) 10.[https://www.facebook.com/share/197KFsCtn6/](https://www.facebook.com/share/197KFsCtn6/) 11.[https://www.facebook.com/share/1c1J7YT3f3/](https://www.facebook.com/share/1c1J7YT3f3/) 12.[https://www.facebook.com/share/1FGB5aYhge/](https://www.facebook.com/share/1FGB5aYhge/) 13.[https://www.facebook.com/share/1BpP5RowST/](https://www.facebook.com/share/1BpP5RowST/) 14.[https://www.facebook.com/share/1BHFA6nR84/](https://www.facebook.com/share/1BHFA6nR84/) 15.[https://www.facebook.com/share/p/192eGfmFV6/](https://www.facebook.com/share/p/192eGfmFV6/) 16.[https://www.facebook.com/share/p/1F3kMa8YLr/](https://www.facebook.com/share/p/1F3kMa8YLr/) 17.[https://www.facebook.com/share/p/1Zcd6D7Z17/](https://www.facebook.com/share/p/1Zcd6D7Z17/) 18.[https://www.facebook.com/share/p/1C212jH2Tq/](https://www.facebook.com/share/p/1C212jH2Tq/) 19.[https://www.facebook.com/share/p/17p6irgRgQ/](https://www.facebook.com/share/p/17p6irgRgQ/) 20.[https://www.facebook.com/share/p/1BwVqtfspS/](https://www.facebook.com/share/p/1BwVqtfspS/) 21.[https://www.facebook.com/share/p/1DYi1yPGjF/](https://www.facebook.com/share/p/1DYi1yPGjF/) 22.[https://www.facebook.com/share/p/19Er1KGqZ1/](https://www.facebook.com/share/p/19Er1KGqZ1/) 23.[https://www.facebook.com/share/p/18sXskazfu/](https://www.facebook.com/share/p/18sXskazfu/) 24.[https://www.facebook.com/share/p/19G15Wweu3/](https://www.facebook.com/share/p/19G15Wweu3/) 25.[https://www.facebook.com/share/p/1CSydX4bGZ/](https://www.facebook.com/share/p/1CSydX4bGZ/) 26.[https://www.facebook.com/share/p/1EcLi1ZDZE/](https://www.facebook.com/share/p/1EcLi1ZDZE/) 27.[https://www.facebook.com/share/p/19dKpLzRew/](https://www.facebook.com/share/p/19dKpLzRew/) 28.[https://www.facebook.com/share/p/1Hdwxo3CLx/](https://www.facebook.com/share/p/1Hdwxo3CLx/) 29.[https://www.facebook.com/share/p/19RxNpwUBR/](https://www.facebook.com/share/p/19RxNpwUBR/) 30.[https://www.facebook.com/share/p/1MAcEDPR8R/](https://www.facebook.com/share/p/1MAcEDPR8R/) 31.[https://www.facebook.com/share/p/196Z36wY5Y/](https://www.facebook.com/share/p/196Z36wY5Y/) 32.[https://www.facebook.com/share/p/1DcjJSNv78/](https://www.facebook.com/share/p/1DcjJSNv78/) 33.[https://www.facebook.com/share/p/18RhTtA1dT/](https://www.facebook.com/share/p/18RhTtA1dT/) 34.[https://www.facebook.com/share/p/1ief3CiBxN/](https://www.facebook.com/share/p/1ief3CiBxN/) 35.[https://www.facebook.com/share/p/1K4pauCorL/](https://www.facebook.com/share/p/1K4pauCorL/) 36.[https://www.facebook.com/share/p/1CugVHnzwr/](https://www.facebook.com/share/p/1CugVHnzwr/) 37.[https://www.facebook.com/share/p/14uz9mpovHU/](https://www.facebook.com/share/p/14uz9mpovHU/) 38.[https://www.facebook.com/share/p/1BLJYtDxUB/](https://www.facebook.com/share/p/1BLJYtDxUB/) 39.[https://www.facebook.com/share/p/14ngrx4zzAf/](https://www.facebook.com/share/p/14ngrx4zzAf/) 40.[https://www.facebook.com/share/p/1Emtcp8ckG/](https://www.facebook.com/share/p/1Emtcp8ckG/) 41.[https://www.facebook.com/share/p/1EzxbbFfyo/](https://www.facebook.com/share/p/1EzxbbFfyo/) 42.[https://www.facebook.com/share/p/19TFdmL6ii/](https://www.facebook.com/share/p/19TFdmL6ii/) 43.[https://www.facebook.com/share/p/1CGYznm6Bt/](https://www.facebook.com/share/p/1CGYznm6Bt/) 44.[https://www.facebook.com/share/p/18uMMNQ6fk/](https://www.facebook.com/share/p/18uMMNQ6fk/) 45.[https://www.facebook.com/share/p/1DKL4kx7UP/](https://www.facebook.com/share/p/1DKL4kx7UP/) 46.[https://www.facebook.com/share/p/19UBACWDUj/](https://www.facebook.com/share/p/19UBACWDUj/) 47.[https://www.facebook.com/share/1EggMgKUUN/](https://www.facebook.com/share/1EggMgKUUN/) 48.[https://www.facebook.com/share/p/1CgDqdNJHd/](https://www.facebook.com/share/p/1CgDqdNJHd/) 49.[https://www.facebook.com/share/p/19dyCNwXjt/](https://www.facebook.com/share/p/19dyCNwXjt/) 50.[https://www.facebook.com/share/p/1BVeTaKWNT/](https://www.facebook.com/share/p/1BVeTaKWNT/) 51.[https://www.facebook.com/share/1Cfj18zJqZ/](https://www.facebook.com/share/1Cfj18zJqZ/) 52.[https://www.facebook.com/share/19UuCbNWLf/](https://www.facebook.com/share/19UuCbNWLf/) 53.[https://www.facebook.com/share/1P1A8VzbPi/](https://www.facebook.com/share/1P1A8VzbPi/) 54.[https://www.facebook.com/share/p/1bBjHvWnjE/](https://www.facebook.com/share/p/1bBjHvWnjE/) 55.[https://www.facebook.com/share/p/1J8HiJxCPV/](https://www.facebook.com/share/p/1J8HiJxCPV/) 56.[https://www.facebook.com/share/p/14preUYdwwy/](https://www.facebook.com/share/p/14preUYdwwy/) 57.[https://www.facebook.com/share/p/1B6vj1vMwT/](https://www.facebook.com/share/p/1B6vj1vMwT/) 58.[https://www.facebook.com/share/p/1EsFiHYjTt/](https://www.facebook.com/share/p/1EsFiHYjTt/) 59.[https://www.facebook.com/share/p/1Kbc3cKynv/](https://www.facebook.com/share/p/1Kbc3cKynv/) 60.[https://www.facebook.com/share/p/1bcAUNU6KM/](https://www.facebook.com/share/p/1bcAUNU6KM/) 61.[https://www.facebook.com/share/p/18u2wqiRtU/](https://www.facebook.com/share/p/18u2wqiRtU/) 62.[https://www.facebook.com/share/p/1HPxPSweeW/](https://www.facebook.com/share/p/1HPxPSweeW/) 63.[https://www.facebook.com/share/p/1E8zyGwMGQ/](https://www.facebook.com/share/p/1E8zyGwMGQ/) 64.[https://www.facebook.com/share/p/1Et969szRQ/](https://www.facebook.com/share/p/1Et969szRQ/) 65.[https://www.facebook.com/share/p/1EdDLGFxnr/](https://www.facebook.com/share/p/1EdDLGFxnr/) 66.[https://www.facebook.com/share/p/18TVVjtJeJ/](https://www.facebook.com/share/p/18TVVjtJeJ/) 67.[https://www.facebook.com/share/p/1DnsfU8LEH/](https://www.facebook.com/share/p/1DnsfU8LEH/) 68.[https://www.facebook.com/share/p/1DXQhVhA9Z/](https://www.facebook.com/share/p/1DXQhVhA9Z/) 69.[https://www.facebook.com/share/p/1EPPWNJoME/](https://www.facebook.com/share/p/1EPPWNJoME/) 70.[https://www.facebook.com/share/p/19ZTaZhijX/](https://www.facebook.com/share/p/19ZTaZhijX/) 71.[https://www.facebook.com/share/p/1C8gsGiqSK/](https://www.facebook.com/share/p/1C8gsGiqSK/) 72.[https://www.facebook.com/share/p/1DUYcxgHLB/](https://www.facebook.com/share/p/1DUYcxgHLB/) 73.[https://www.facebook.com/share/p/19de7k9jfh/](https://www.facebook.com/share/p/19de7k9jfh/) 74.[https://www.facebook.com/share/p/1EXrZrbkvu/](https://www.facebook.com/share/p/1EXrZrbkvu/) 75.[https://www.facebook.com/share/p/1Gces56Qen/](https://www.facebook.com/share/p/1Gces56Qen/) 76.[https://www.facebook.com/share/p/1Qq17661G7/](https://www.facebook.com/share/p/1Qq17661G7/) 77.[https://www.facebook.com/share/p/1FVnrChDgd/](https://www.facebook.com/share/p/1FVnrChDgd/) 78.[https://www.facebook.com/share/p/1DenAgSQYS/](https://www.facebook.com/share/p/1DenAgSQYS/) 79.[https://www.facebook.com/share/p/1DHhSQ2dnb/](https://www.facebook.com/share/p/1DHhSQ2dnb/) 80.[https://www.facebook.com/share/p/1EFyFVoFLt/](https://www.facebook.com/share/p/1EFyFVoFLt/) 81.[https://www.facebook.com/share/p/1C1k7XP7tE/](https://www.facebook.com/share/p/1C1k7XP7tE/) 82.[https://www.facebook.com/share/p/1DrUUBr6fK/](https://www.facebook.com/share/p/1DrUUBr6fK/) 83.[https://www.facebook.com/share/p/1BVh5bp6kQ/](https://www.facebook.com/share/p/1BVh5bp6kQ/) 84.[https://www.facebook.com/share/p/1BxEPx2hj7/](https://www.facebook.com/share/p/1BxEPx2hj7/) 85.[https://www.facebook.com/share/p/19akz97c4T/](https://www.facebook.com/share/p/19akz97c4T/) 86.[https://www.facebook.com/share/p/1Dpj89g2mf/](https://www.facebook.com/share/p/1Dpj89g2mf/) 87.[https://www.facebook.com/share/p/1EZC541bXG/](https://www.facebook.com/share/p/1EZC541bXG/) 88.[https://www.facebook.com/share/p/1CvMeBLv1Y/](https://www.facebook.com/share/p/1CvMeBLv1Y/) 89.[https://www.facebook.com/share/p/1Jxmrr45aM/](https://www.facebook.com/share/p/1Jxmrr45aM/) 90.[https://www.facebook.com/share/p/19wCsA4Uo2/](https://www.facebook.com/share/p/19wCsA4Uo2/) 91.[https://www.facebook.com/share/p/1CRTqfnmri/](https://www.facebook.com/share/p/1CRTqfnmri/) 92.[https://www.facebook.com/share/p/14rooqS55z4/](https://www.facebook.com/share/p/14rooqS55z4/) 93.[https://www.facebook.com/share/p/19gr2bT544/](https://www.facebook.com/share/p/19gr2bT544/)
"""

urls = extract_all_facebook_urls(raw_user_text)
print(f"Total URLs to extract: {len(urls)}")

output_dir = r"c:\Users\NADID\Desktop\Anything extractor\extracted_novel"
os.makedirs(output_dir, exist_ok=True)
chapters_dir = os.path.join(output_dir, "chapters")
os.makedirs(chapters_dir, exist_ok=True)

extractor = FacebookExtractor()
all_compiled_text = []
metadata_list = []
total_words = 0

start_time = time.time()

for idx, u in enumerate(urls, 1):
    print(f"[{idx}/{len(urls)}] Extracting {u} ... ", end="", flush=True)
    try:
        data = extractor.extract(u)
        text = data.get("text", "")
        title = data.get("title") or f"Chapter {idx}"
        words = len(text.split()) if text else 0
        total_words += words
        
        # Save individual chapter file
        ch_filename = os.path.join(chapters_dir, f"Chapter_{idx:02d}.txt")
        ch_content = f"============================================================\n"
        ch_content += f"Part {idx}: {title}\n"
        ch_content += f"URL: {data.get('url')}\n"
        ch_content += f"Words: {words} | Characters: {len(text)}\n"
        ch_content += f"============================================================\n\n"
        ch_content += text if text else "[No text could be extracted for this post]"
        ch_content += "\n\n"

        with open(ch_filename, "w", encoding="utf-8") as f:
            f.write(ch_content)

        all_compiled_text.append(ch_content)
        metadata_list.append({
            "part": idx,
            "url": u,
            "resolved_url": data.get("url"),
            "title": title,
            "words": words,
            "characters": len(text),
            "images_count": len(data.get("images", [])),
            "image_urls": [img["url"] for img in data.get("images", [])]
        })
        print(f"OK ({len(text)} chars, {words} words)")
    except Exception as e:
        print(f"ERROR: {e}")

# Save full compiled book
full_book_path = os.path.join(output_dir, "The_Bloody_Queen_Of_The_Crimson_Moon_Full_Novel.txt")
with open(full_book_path, "w", encoding="utf-8") as f:
    f.write(f"THE BLOODY QUEEN OF THE CRIMSON MOON\n")
    f.write(f"Full Series Compilation ({len(urls)} Parts, {total_words:,} Total Words)\n")
    f.write(f"{'='*60}\n\n")
    f.write("\n".join(all_compiled_text))

# Save metadata json
meta_path = os.path.join(output_dir, "series_metadata.json")
with open(meta_path, "w", encoding="utf-8") as f:
    json.dump({
        "total_parts": len(urls),
        "total_words": total_words,
        "parts": metadata_list
    }, f, indent=2, ensure_ascii=False)

elapsed = time.time() - start_time
print("\n" + "="*60)
print(f"EXTRACTION COMPLETE in {elapsed:.1f}s!")
print(f"Total parts: {len(urls)}")
print(f"Total words: {total_words:,}")
print(f"Full Novel File: {full_book_path}")
print(f"Individual Chapters Folder: {chapters_dir}")
print("="*60)
