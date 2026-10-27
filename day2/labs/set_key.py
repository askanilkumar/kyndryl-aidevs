"""Save your OpenAI key ONCE, outside the repo:  python set_key.py
It is written to  ~/.askrag.env  (your home folder), so git can never push it."""
import getpass, os
path = os.path.join(os.path.expanduser("~"), ".askrag.env")
key = getpass.getpass("Paste the OpenAI key (typing is hidden), then press Enter: ").strip()
if not key.startswith("sk-"):
    raise SystemExit("That does not look like a key (it should start with sk-). Nothing saved.")
with open(path, "w") as f:
    f.write("OPENAI_API_KEY=" + key + "\n")
print("Saved to", path, "- now run: python check_setup.py")
