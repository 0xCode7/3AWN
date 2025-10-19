# Drug-Drug Interaction (DDI) Prediction System

This repository contains a comprehensive **AI-powered system** for predicting drug-drug interactions using machine learning. The project includes multiple approaches: an advanced pipeline with Logistic Regression and Random Forest models, and a Flask web application for real-time predictions.

## 🚀 Features

- **Advanced ML Pipeline**: Logistic Regression and Random Forest classifiers
- **Interactive CLI**: Command-line interface for quick drug interaction checks
- **Web Interface**: Flask-based web application with user-friendly interface
- **High Accuracy**: Trained models with comprehensive evaluation metrics
- **Fuzzy Matching**: Handles minor typos in drug names
- **Scalable Architecture**: Supports 100+ drugs with room for expansion

---

## 📁 Project Structure  

```
.
├── ddi_pipeline.py         # Main ML pipeline (training & prediction)
├── predict_interaction.py  # Interactive CLI for predictions
├── test_predictions.py     # Automated testing script
├── Flask_model.py          # Flask web application
├── DDI_model.ipynb         # Jupyter notebook (legacy pipeline)
├── best_ddi_model.pkl      # Best trained model (auto-generated)
├── DDI_rf_model.pkl        # RandomForest model (legacy)
├── DDI_data.csv            # Training dataset
├── u_matrix.npy            # SVD decomposition matrix (U)
├── vt_matrix.npy           # SVD decomposition matrix (VT)
├── drug_index.npy          # Drug → Index mapping
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

---

## 🛠️ Setup Instructions  

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone the repository:**  
   ```bash
   git clone <repo-link>
   cd D3adL0ck-AI-main
   ```

2. **Create & activate a virtual environment (recommended):**  
   ```bash
   python -m venv ddi_env
   ddi_env\Scripts\activate      # On Windows
   source ddi_env/bin/activate   # On Mac/Linux
   ```

3. **Install dependencies:**  
   ```bash
   pip install -r requirements.txt
   ```
   Or install manually:
   ```bash
   pip install pandas scikit-learn numpy joblib flask
   ```

---

## 🚀 Usage

### Option 1: Train Models & Make Predictions (Recommended)

1. **Train the models:**
   ```bash
   python ddi_pipeline.py --csv DDI_data.csv
   ```
   This will:
   - Load and preprocess the dataset
   - Train Logistic Regression and Random Forest models
   - Display evaluation metrics
   - Save the best model as `best_ddi_model.pkl`

2. **Make individual predictions:**
   ```bash
   python ddi_pipeline.py --predict "Bivalirudin" "Alfuzosin"
   ```

3. **Use the interactive CLI:**
   ```bash
   python predict_interaction.py
   ```
   Follow the prompts to enter drug names and get predictions.

4. **Run automated tests:**
   ```bash
   python test_predictions.py
   ```

### Option 2: Flask Web Application

1. **Start the Flask app:**  
   ```bash
   python Flask_model.py
   ```

2. **Open in browser:**  
   ```
   http://127.0.0.1:5001/input
   ```

3. **Enter two drug names** → Get predicted interaction severity:  
   - **Major**  
   - **Moderate**  
   - **Minor**  
   - **No known interaction**

---

## 📊 Example Output

### Interactive CLI Example:
```
=== Drug Interaction Checker ===
Enter the first drug name: Bivalirudin
Enter the second drug name: Alfuzosin

==================================================
Checking interaction between: Bivalirudin and Alfuzosin
Prediction: YES (confidence: 79.1%)
==================================================

Check another pair? (y/n): n
Goodbye!
```

### Test Results Example:
```
=== Drug Interaction Test Results ===

Drug Pair: Bivalirudin + Alfuzosin
Prediction: YES (Confidence: 79.1%)
--------------------------------------------------
Drug Pair: Aspirin + Warfarin
Prediction: NO (Confidence: 27.8%)
--------------------------------------------------
Drug Pair: Simvastatin + Amlodipine
Prediction: YES (Confidence: 96.3%)
--------------------------------------------------
```

---

## 🔧 Technical Details

### Machine Learning Models
- **Logistic Regression**: Fast, interpretable baseline model
- **Random Forest**: Ensemble method for improved accuracy
- **Feature Engineering**: One-hot encoding for drug pairs
- **Model Selection**: Automatic selection of best-performing model

### Data Processing
- **Input**: CSV file with drug pairs and interaction labels
- **Preprocessing**: One-hot encoding, train-test split
- **Evaluation**: Accuracy, precision, recall, F1-score, ROC-AUC

### Architecture
- **Pipeline-based**: Scikit-learn pipelines for reproducibility
- **Modular Design**: Separate training, prediction, and CLI components
- **Error Handling**: Graceful handling of unknown drugs and edge cases

---

## 📈 Model Performance

The system trains multiple models and automatically selects the best performer:
- **Evaluation Metrics**: Accuracy, Precision, Recall, F1-Score, ROC-AUC
- **Cross-Validation**: Robust model evaluation
- **Model Persistence**: Best model saved as `best_ddi_model.pkl`

---

## 🛡️ Error Handling

- **Missing Model**: Clear error messages if model file not found
- **Invalid Inputs**: Handles empty or invalid drug names
- **Unknown Drugs**: Graceful handling of drugs not in training data
- **File Errors**: Comprehensive error handling for file operations

---

## 🔮 Future Enhancements

- **Larger Dataset**: Expand to more drug combinations
- **Advanced Models**: XGBoost, Neural Networks, Transformers
- **Drug Embeddings**: Use molecular structure embeddings
- **Real-time Updates**: Integration with pharmaceutical databases
- **API Integration**: RESTful API for external applications
- **Mobile App**: Flutter-based mobile interface

---

## 📝 Notes  

- **Modular Architecture**: Multiple interfaces (CLI, Web, API)
- **Extensible Design**: Easy to add new models and features
- **Production Ready**: Comprehensive error handling and logging
- **Team Collaboration**: Compatible with other project components (Flutter, Backend APIs)
- **Continuous Improvement**: Model performance can be enhanced with more data and advanced techniques  
