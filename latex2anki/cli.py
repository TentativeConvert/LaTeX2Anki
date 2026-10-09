import argparse
import subprocess
import sys
import tempfile
from pathlib import Path
# for html to csv conversion:
import csv
import re
from bs4 import BeautifulSoup
# for handling images:
import hashlib
import shutil


# The following template is passed to plastex to convert latex to html:
JINJA_TEMPLATE_FOR_PLASTEX = """\
name: note
<div class="note">
     <div class="uuid">{{ obj.attributes.uuid }}</div>
     {{ obj }}
</div>
"""

def fail(message):
    print("\nERROR: " + message, file=sys.stderr)
    sys.exit(1)

def main():
    ##################################################
    # STEP 0:  Process arguments and define file names

    parser = argparse.ArgumentParser(description="Conversion script: LaTeX --plastex--> HTML --python--> csv-file for Anki")
    parser.add_argument("texfile", help="LaTeX file to process")
    parser.add_argument("--anki-profile", metavar="PROFILE_DIR",
                        help="Anki profile folder (e.g. '~/.local/share/Anki2/User 1'); "
                             "if given, images are also copied to its subfolder collection.media")
    args = parser.parse_args()

    tex_path = Path(args.texfile)                      # (Path object describing texfile supplied by user)
    STEM        = tex_path.stem
    INPUT_FILE  = str(tex_path)
    HTML_FILENAME = STEM + ".html"
    HTML_DIR    = tex_path.parent / (STEM + "-html")   # html preview, including images subfolder
    CSV_DIR     = tex_path.parent / (STEM + "-csv")    # csv file and renamed images for Anki
    HTML_FILE   = HTML_DIR / HTML_FILENAME
    OUTPUT_FILE = CSV_DIR / (STEM + ".csv")
    EXTRA_CSS_FILE = "MathCloze.css" # plastex copies this file to "[outputdir]/styles"
    EXTRA_JS_FILE  = "MathCloze.js"  # plastex copies this file to "[outputdir]/js"

    if args.anki_profile:
        MEDIA_DIR = Path(args.anki_profile).expanduser() / "collection.media"
        if not MEDIA_DIR.is_dir():
            fail(f"{MEDIA_DIR} does not exist.  The argument of --anki-profile should be "
                 "an Anki profile folder, i.e. a folder containing collection.media.")

    ##################################################
    # STEP 1: LaTeX to HTML
    print("\nSTEP 1: Converting " + INPUT_FILE + " to " + str(HTML_FILE) + " via plastex...\n")

    # Remove old html file, so that we never convert a stale html file to csv
    HTML_FILE.unlink(missing_ok=True)

    with tempfile.TemporaryDirectory() as TEMP_TEMPLATE_DIR:
        # Create temporary file with the template from above
        template_path = Path(TEMP_TEMPLATE_DIR) / "latex2anki.jinja2s"
        template_path.write_text(JINJA_TEMPLATE_FOR_PLASTEX, encoding="utf-8")
        # Call plastex, passing the folder in which the template lives as an argument
        result = subprocess.run(["plastex", f"--extra-templates={TEMP_TEMPLATE_DIR}", "--no-theme-css", f"--extra-css={EXTRA_CSS_FILE}",f"--extra-js={EXTRA_JS_FILE}",f"--dir={HTML_DIR}",f"--filename={HTML_FILENAME}", INPUT_FILE])

    if result.returncode != 0 or not HTML_FILE.exists():
        fail(f"plastex failed (exit code {result.returncode}), see its output above.")

    ##################################################
    # STEP 2: HTML to csv
    print("\nSTEP 2: Converting "+ str(HTML_FILE) + " to " + str(OUTPUT_FILE) + "...\n")
    # Start from an empty csv folder, so that no stale images are left over
    if CSV_DIR.exists():
        shutil.rmtree(CSV_DIR)
    (CSV_DIR / "images").mkdir(parents=True)

    # Read the HTML file
    with open(HTML_FILE, "r", encoding="utf-8") as f:
        html_doc = f.read()

    # Parse the HTML
    soup = BeautifulSoup(html_doc, "html.parser")

    # Find all divs with class "note"
    notes = soup.find_all("div", class_="note")
    if not notes:
        fail(f"No notes found in {HTML_FILE}.  Is MathCloze.ini in the folder of {INPUT_FILE}?")

    csv_rows = []
    images = {}  # new image file name -> path of image in csv folder

    # Post-process notes:
    for note in notes:
        # Work on the inner HTML of each note
        inner = BeautifulSoup(note.decode_contents(), "html.parser")

        # Extract UUID
        uuid_div = inner.find("div", class_="uuid")
        if uuid_div:
            uuid_field = uuid_div.get_text(strip=True)
            uuid_div.decompose()  # remove the uuid div from the note
        else:
            uuid_field = ""
            print("ERROR: There's a note without a UUID.")

        # Images (e.g. tikz-cd diagrams): Anki's media folder is flat and shared by
        # all decks, so copy each image to the csv folder under the unique name
        # [STEM]-[hash of contents].[ext] and refer to it by this bare name.
        for img in inner.find_all("img"):
            src_path = HTML_DIR / img["src"]
            if not src_path.is_file():
                fail(f"Image {src_path} not found.")
            digest = hashlib.sha256(src_path.read_bytes()).hexdigest()[:12]
            new_name = f"{STEM}-{digest}{src_path.suffix}"
            if new_name not in images:
                images[new_name] = CSV_DIR / "images" / new_name
                shutil.copyfile(src_path, images[new_name])
            img["src"] = new_name
            # the alt text is the LaTeX source of the image, which only bloats the csv
            # and puts LaTeX braces into clozes
            if img.has_attr("alt"):
                del img["alt"]

        # Split remaining content at each "((FIELDSEPARATOR))"
        raw_fields = str(inner).split("((FIELDSEPARATOR))")
        # Overwrite first (empty) field with UUID:
        raw_fields[0] = uuid_field

        #print(raw_fields)

        parsed_fields = [BeautifulSoup(f,"html.parser") for f in raw_fields]
        cleaned_fields = []
        for field in parsed_fields:
            # Clean up: remove newlines and collapse spaces
            cleaned_field = field.decode_contents().replace("\n", "").strip() # remove linebreaks
            # Insert whitespaces between consecutive curly braces, so Anki
            # does not misread them as closing a cloze deletion
            # i.e.:
            # }}  --> } }
            # }}} --> } } }
            # etc.
            cleaned_field = re.sub(r"(?<=})}", " }", cleaned_field)
            # Replace manual CLOZE markup with Anki's cloze-syntax
            cleaned_field = re.sub(r'\(\(CLOZE(\d+)\)\)', r'{{c\1::', cleaned_field)
            cleaned_field = re.sub(r'\(\(HINT\)\)', '::', cleaned_field)
            cleaned_field = re.sub(r'\(\(CLEND\)\)', '}}', cleaned_field)

            cleaned_fields.append(cleaned_field)

        #print(cleaned_fields)
        csv_rows.append(cleaned_fields)

    # Write to CSV file
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter='|', quoting=csv.QUOTE_MINIMAL,lineterminator='\n')
        # Write header lines
        f.write("#separator:|\n")
        f.write("#html:true\n")
        # Write rows
        writer.writerows(csv_rows)

    print(f"Wrote {len(csv_rows)} rows to {OUTPUT_FILE}")
    print(f"Wrote {len(images)} images to {CSV_DIR / 'images'}")

    ##################################################
    # STEP 3 (optional): copy images to Anki's media folder
    if args.anki_profile:
        print("\nSTEP 3: Copying images to " + str(MEDIA_DIR) + "...\n")
        copied = 0
        for name, path in images.items():
            target = MEDIA_DIR / name
            # Names are content hashes, so an existing file with the same name is
            # (almost certainly) the same image.  Never overwrite anything in Anki.
            if not target.exists():
                shutil.copyfile(path, target)
                copied += 1
        print(f"Copied {copied} new images ({len(images) - copied} were already there).")


if __name__ == "__main__":
    main()
