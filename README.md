# UMAP Text Explorer

A Streamlit app for exploring two-dimensional embeddings or other coordinate data in a CSV file, with flexible coloring, filtering, and point inspection options.

## What this app does

This app is designed for interactive exploration of precomputed 2D coordinates. It lets you:

- upload a CSV file with coordinate columns such as:
  - `x` / `y`
  - `x_profile_reduced` / `y_profile_reduced`
  - `x_ss` / `y_ss`
  - `x_ds` / `y_ds`
- choose which coordinate pair to visualize
- select which text column to inspect in the hover tooltip and selection panel
- color points by:
  - a metadata column
  - goal of advertisement
  - location publisher
  - age groups
  - religion columns
  - term blend categories
  - literal term matching in the selected text column
- filter by year
- animate a moving year window
- inspect selected points and their associated text

This makes the app useful for exploring how different embedding variants or representations compare visually, and for examining whether clusters or local structure change when using different coordinate systems.

Typical use cases include:

- comparing original vs. profile-reduced embeddings
- comparing OCR, SS, and DS text representations
- exploring whether coordinate structure aligns with metadata groups
- highlighting records containing particular linguistic patterns via regex
- inspecting selected points directly in the original text

The app is especially useful for historical text datasets where multiple coordinate systems and metadata layers are available.

---

## Public app

You can use the public app here:

**https://umaptextexplorer.streamlit.app**

Upload the csv datasets you can find in this repository _(not yet publicly available)_.

If the public app is temporarily unavailable, slow, or has too many users, you can run your own copy locally or deploy your own version online.

---

## Expected data format

The app assumes that your dataset already contains coordinate columns that form valid pairs.

Current supported coordinate pairs:

- `x` and `y`
- `x_profile_reduced` and `y_profile_reduced`
- `x_ss` and `y_ss`
- `x_ss_profile_reduced` and `y_ss_profile_reduced`
- `x_ds` and `y_ds`
- `x_ds_profile_reduced` and `y_ds_profile_reduced`

With at least one of the following column names:

- `OCR extended`
- `SS extended`
- `DS extended`

## Term matching
The app can color points based on whether the selected text column matches one or more literal search terms.

There are two matching modes:

- `Term contains`: Matches rows where the selected text column contains the entered value as a literal substring.
- `Term is exact token`: Matches rows where the selected text column contains the entered value as a complete token or word.

---

## How to run the app locally

### 1. Clone this repository

    git clone https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git
    cd YOUR-REPO-NAME

### 2. Create and activate a virtual environment

Mac / Linux:

    python -m venv .venv
    source .venv/bin/activate

Windows:

    python -m venv .venv
    .venv\Scripts\activate

### 3. Install dependencies

    pip install -r requirements.txt


### 4. Start the app

    streamlit run appText.py

Your browser should open automatically. If not, Streamlit will print a local URL such as:

    http://localhost:8501

## How to make your own version

You are very welcome to copy this repository and adapt it for your own project.

### Option 1: Fork this repository

If you want to keep a visible link to the original repository, click **Fork** on GitHub.

### Option 2: Copy the code into your own repository

If you want a fully independent version, create a new repository and copy the files there.

### Typical reasons to make your own version

You may want to:

- adjust the interface
- change the coordinate-pair names or defaults
- add more filtering options
- add more metadata-driven color schemes
- modify the regex matching behavior
- support a different dataset structure

Or simply because:

- the public app has too many users or is temporarily unavailable
- you want your own stable deployment

## How to deploy your own Streamlit app

The easiest way is with **Streamlit Community Cloud**.

### 1. Push your code to GitHub

Make sure your repository includes at least:

- `app.py`
- `requirements.txt`

### 2. Go to Streamlit Community Cloud

Open: **https://share.streamlit.io**

### 3. Sign in with GitHub

### 4. Create a new app

Select:

- your repository
- the branch
- the main file, usually `app.py`

### 5. Deploy

After deployment, Streamlit will give you your own app URL.

---

## Citation

If you use this app or adapt the code, please cite the repository and, once available, the accompanying paper.

    Hoek, L. UMAP Text Explorer, 2026. https://github.com/LisaHoek/UMAPtextExplorer

Future paper citation:
To be added here.

## License
This project is licensed under \<placeholder\>.

## Contact
If you have any questions, please contact me using the contact details on my personal webpage: **https://hookedondata.nl**.