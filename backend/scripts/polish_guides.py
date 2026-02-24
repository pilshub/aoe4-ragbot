"""Read Vortix's .odt civilization guides, polish with GPT-4o, save as .md files.

Usage:
    cd backend
    python -m scripts.polish_guides
    python -m scripts.polish_guides --dry-run        # Show raw text, don't call GPT
    python -m scripts.polish_guides --only Frances    # Process only one file
"""

import argparse
import os
import sys
import time

from odf.opendocument import load as load_odt
from odf.text import P, H

# Map .odt filenames (without extension) to canonical civ info
CIV_MAP = {
    "Abasidas": ("abbasid_dynasty", "Abbasid Dynasty", "Dinastía Abasí"),
    "Ayubi": ("ayyubids", "Ayyubids", "Ayubíes"),
    "Bizantinos": ("byzantines", "Byzantines", "Bizantinos"),
    "Chinos": ("chinese", "Chinese", "Chinos"),
    "Delhi": ("delhi_sultanate", "Delhi Sultanate", "Sultanato de Delhi"),
    "Frances": ("french", "French", "Franceses"),
    "Horda": ("golden_horde", "Golden Horde", "Horda de Oro"),
    "Ingles": ("english", "English", "Ingleses"),
    "Japones": ("japanese", "Japanese", "Japoneses"),
    "Juana": ("jeannes_darc", "Jeanne d'Arc", "Juana de Arco"),
    "Lancaster": ("house_of_lancaster", "House of Lancaster", "Casa de Lancaster"),
    "Macedonios": ("macedonian_dynasty", "Macedonian Dynasty", "Dinastía Macedonia"),
    "Malienses": ("malians", "Malians", "Malienses"),
    "Mongoles": ("mongols", "Mongols", "Mongoles"),
    "Orden": ("order_of_the_dragon", "Order of the Dragon", "Orden del Dragón"),
    "Otomanos": ("ottomans", "Ottomans", "Otomanos"),
    "Rus": ("rus", "Rus", "Rus"),
    "Sacro": ("holy_roman_empire", "Holy Roman Empire", "Sacro Imperio Romano"),
    "Sengoku": ("sengoku_daimyo", "Sengoku Daimyo", "Sengoku Daimyo"),
    "Templarios": ("knights_templar", "Knights Templar", "Caballeros Templarios"),
    "Tughlaq": ("tughlaq_dynasty", "Tughlaq Dynasty", "Dinastía Tughlaq"),
    "Zhuxi": ("zhuxis_legacy", "Zhu Xi's Legacy", "Legado de Zhu Xi"),
}

GUIDES_DIR = r"C:\Users\fermi\Desktop\guias aoe4"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "guides")

POLISH_PROMPT = """\
Eres un editor de contenido de videojuegos. Recibes las notas RAW de un jugador profesional de Age of Empires IV (Vortix) sobre cómo jugar una civilización. Tu tarea es convertir estas notas en prosa fluida y bien estructurada.

REGLAS ESTRICTAS:
1. NO añadas información nueva. Si el original dice "Keshik rápido", tú puedes decir "Producir Keshik lo antes posible al subir a segunda edad" — pero NO inventes datos que no estén en el original.
2. NO elimines información. Todo lo que esté en el original debe aparecer en tu versión.
3. Mantén el idioma ESPAÑOL.
4. Convierte las notas telegráficas en frases completas y naturales.
5. Cada sección debe empezar con un header markdown (## para edades/fases principales, ### para subsecciones como matchups).
6. El primer header debe ser: ## Guía de Vortix — {civ_name_es} ({civ_name_en})
7. Añade contexto implícito donde sea necesario. Si una sección habla de "subir con Escuela de Caballería", asegúrate de que quede claro que es un landmark y de qué edad.
8. La línea de stats final (Agresión: X, Defensa: Y, etc.) formateala como una sección ### Valoración de Vortix con cada stat en su propia línea.
9. Los matchups deben tener ### con el nombre descriptivo: ### Contra civilizaciones agresivas (Franceses, Rus, etc.)
10. NO uses emojis en los headers.
11. El tono debe ser directo, como un coach explicando a un alumno. No uses lenguaje excesivamente formal ni coloquial.
12. Cuando el original menciona nombres abreviados de civilizaciones (FR, Sacro, Ayu, Japo), expándelos al nombre completo.

CIVILIZACIÓN: {civ_name_es} ({civ_name_en})

NOTAS RAW DE VORTIX:
{raw_content}

Devuelve SOLO el markdown pulido, sin explicaciones ni comentarios adicionales."""


def extract_odt_text(filepath: str) -> str:
    """Extract text from .odt file preserving headers and paragraphs."""
    doc = load_odt(filepath)

    def get_text(node) -> str:
        result = ""
        for child in node.childNodes:
            if hasattr(child, "childNodes") and child.childNodes:
                result += get_text(child)
            else:
                result += str(child)
        return result

    parts = []

    # Collect header element IDs for quick lookup
    headers = doc.getElementsByType(H)
    header_ids = {id(h) for h in headers}

    # Process all elements in order
    for elem in doc.text.childNodes:
        text = get_text(elem).strip()
        if not text:
            continue

        if id(elem) in header_ids:
            level = int(elem.getAttribute("outlinelevel") or "1")
            # Strip emojis from start of header
            clean = text.lstrip()
            while clean and ord(clean[0]) > 0x2000:
                clean = clean[1:].lstrip()
            hashes = "#" * (level + 1)  # H1 -> ##, H2 -> ###, H3 -> ####
            parts.append(f"\n{hashes} {clean}\n")
        else:
            parts.append(text)

    return "\n".join(parts)


def polish_with_gpt(raw_content: str, civ_name_en: str, civ_name_es: str) -> str:
    """Polish raw guide content using GPT-4o."""
    from openai import OpenAI

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

    prompt = POLISH_PROMPT.format(
        civ_name_en=civ_name_en,
        civ_name_es=civ_name_es,
        raw_content=raw_content,
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=4000,
    )

    return response.choices[0].message.content.strip()


def main():
    parser = argparse.ArgumentParser(description="Polish Vortix's AoE4 civ guides")
    parser.add_argument("--dry-run", action="store_true", help="Extract text only, don't call GPT")
    parser.add_argument("--only", type=str, help="Process only this filename (without .odt)")
    args = parser.parse_args()

    # Load .env
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    load_dotenv(env_path)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    files = sorted(os.listdir(GUIDES_DIR))
    odt_files = [f for f in files if f.endswith(".odt")]

    if args.only:
        odt_files = [f for f in odt_files if f.replace(".odt", "") == args.only]
        if not odt_files:
            print(f"File '{args.only}.odt' not found in {GUIDES_DIR}")
            sys.exit(1)

    print(f"Found {len(odt_files)} guide files\n")

    for filename in odt_files:
        name = filename.replace(".odt", "")
        if name not in CIV_MAP:
            print(f"  SKIP {filename} — not in CIV_MAP")
            continue

        civ_id, civ_en, civ_es = CIV_MAP[name]
        filepath = os.path.join(GUIDES_DIR, filename)

        print(f"  Processing: {filename} → {civ_en} ({civ_es})")

        # Extract raw text
        raw = extract_odt_text(filepath)
        print(f"    Raw text: {len(raw)} chars")

        if args.dry_run:
            print(f"    --- RAW CONTENT ---")
            print(raw[:500])
            print(f"    --- (truncated) ---\n")
            continue

        # Polish with GPT
        print(f"    Polishing with GPT-4o...", end=" ", flush=True)
        start = time.time()
        polished = polish_with_gpt(raw, civ_en, civ_es)
        elapsed = time.time() - start
        print(f"done ({elapsed:.1f}s, {len(polished)} chars)")

        # Save
        output_path = os.path.join(OUTPUT_DIR, f"{civ_id}.md")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(polished)
        print(f"    Saved: {output_path}\n")

        # Small delay to avoid rate limits
        time.sleep(0.5)

    if not args.dry_run:
        print(f"\nAll guides polished and saved to {OUTPUT_DIR}")
    else:
        print(f"\nDry run complete. Use without --dry-run to polish with GPT.")


if __name__ == "__main__":
    main()
