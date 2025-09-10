import argparse  
import subprocess
import tempfile
from pathlib import Path
# for html to csv conversion:
import csv
import re
from bs4 import BeautifulSoup


# The following template is passed to plastex to convert latex to html:
JINJA_TEMPLATE_FOR_PLASTEX = """\
name: note
<div class="note">
     <div class="uuid">{{ obj.attributes.uuid }}</div>
     {{ obj }}
</div>

name: field 
<br class="fieldseparator"></br>
"""

def main():
    ##################################################
    # STEP 0:  Process arguments and define file names
    
    parser = argparse.ArgumentParser(description="Conversion script: LaTeX --plastex--> HTML --python--> csv-file for Anki")
    parser.add_argument("texfile", help="LaTeX file to process")
    args = parser.parse_args()
    
    tex_path = Path(args.texfile)                      # (Path object describing texfile supplied by user)
    INPUT_FILE  = str(tex_path)     
    HTML_FILENAME = str(tex_path.stem + ".html")
    HTML_FILE   = str(Path(tex_path.parent / tex_path.stem / tex_path.stem).with_suffix(".html"))
    OUTPUT_FILE = str(Path(tex_path.parent / tex_path.stem / tex_path.stem).with_suffix(".csv"))

    ##################################################
    # STEP 1: LaTeX to HTML 
    print("\nSTEP 1: Converting " + INPUT_FILE + " to " + HTML_FILE + " via plastex...\n")

    with tempfile.TemporaryDirectory() as TEMP_TEMPLATE_DIR:
        # Create temporary file with the template from above
        template_path = Path(TEMP_TEMPLATE_DIR) / "latex2anki.jinja2s"
        template_path.write_text(JINJA_TEMPLATE_FOR_PLASTEX, encoding="utf-8")
        # Call plastex, passing the folder in which the template lives as an argument
        subprocess.run(["plastex", f"--extra-templates={TEMP_TEMPLATE_DIR}", f"--filename={HTML_FILENAME}", INPUT_FILE])
        
    ##################################################
    # STEP 2: HTML to csv
    print("\nSTEP 2: Converting "+ HTML_FILE + " to " + OUTPUT_FILE + "...\n")
    # Read the HTML file
    with open(HTML_FILE, "r", encoding="utf-8") as f:
        html_doc = f.read()
        
    # Parse the HTML
    soup = BeautifulSoup(html_doc, "html.parser")
    
    # Find all divs with class "note"
    notes = soup.find_all("div", class_="note")
    
    csv_rows = []
    
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

        # Split remaining content by <br class="fieldseparator">
        # Find all field separators:
        for sep in inner.find_all("br", class_="fieldseparator"):
            # Replace <br class="fieldseparator"> with normalized marker '|'
            # (BeautifulSoup normalizes <br class="fieldseparator"></br> to <br class="fieldseparator"></br>,
            # so it's safer to use BeautifulSoup to replace the html markup by a different marker before splitting the string
            # rather than splitting the string directly using the html markup.
            sep.replace_with("###FIELDSEPARATOR###")

        raw_fields = str(inner).split("###FIELDSEPARATOR###")
        # Overwrite first (empty) field with UUID:
        raw_fields[0] = uuid_field

        #print(raw_fields)
        
        parsed_fields = [BeautifulSoup(f,"html.parser") for f in raw_fields]
        cleaned_fields = []
        for field in parsed_fields:
            # Clean up: remove newlines and collapse spaces
            cleaned_field = field.decode_contents().replace("\n", "").strip() # remove linebreaks
            
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

    
if __name__ == "__main__":
    main()
