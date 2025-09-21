Drug-Drug Interaction Model

This repository contains the **AI part** of our project for predicting drug–drug interactions.  
It includes data preprocessing, model training, and a Flask backend for serving predictions.  


---

## Project Structure  

```
.
├── DDI_model.ipynb        # Jupyter notebook (training pipeline)
├── Flask_model.py         # Flask app for predictions
├── DDI_rf_model.pkl       # Trained RandomForest model
├── u_matrix.npy           # SVD decomposition matrix (U)
├── vt_matrix.npy          # SVD decomposition matrix (VT)
├── drug_index.npy         # Drug → Index mapping
├── requirements.txt       # Python dependencies
└── README.md              # Project documentation
```

---

##  Setup Instructions  

1. Clone the repository:  
   ```bash
   git clone <repo-link>
   cd <repo-folder>
   ```

2. Create & activate a virtual environment (recommended):  
   ```bash
   python -m venv venv
   venv\Scripts\activate      # On Windows
   source venv/bin/activate   # On Mac/Linux
   ```

3. Install dependencies:  
   ```bash
   pip install -r requirements.txt
   ```

---

##  Run the Flask App  

1. Start the app:  
   ```bash
   python Flask_model.py
   ```

2. Open in browser:  
   ```
   http://127.0.0.1:5001/input
   ```

3. Enter two drug names → Get predicted interaction severity:  
   - **Major**  
   - **Moderate**  
   - **Minor**  
   - **No known interaction**

---

##  Features  

- Trained on drug–drug interaction dataset.  
- Uses **SVD** embeddings + **RandomForestClassifier**.  
- Handles missing drugs gracefully (error message).  
- Added **fuzzy matching** to correct minor typos in drug names.  
- Scaled dataset from **5 drugs → 100+ drugs**.  
- Compatible with **Neo4j dataset backend** (for future extensions).  

---

##  Notes  

- This repo covers **AI module only**.  
- Other team members will push their own repos (Flutter, Backend APIs, etc.).  
- Model accuracy is ~28% (baseline). Can be improved with bigger dataset + advanced models (XGBoost, Neural Nets).  
