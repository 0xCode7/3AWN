"""
Drug-Drug Interaction Prediction CLI

This script loads a pre-trained model and allows users to check for potential
drug interactions between two medications.
"""
import os
from typing import Tuple
from ddi_pipeline import predict_interaction  # Import the prediction function

def check_model_exists(model_path: str = 'best_ddi_model.pkl'):
    """Check if the pre-trained model exists."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file '{model_path}' not found. Please train the model first.")
    return True

def get_user_input() -> Tuple[str, str]:
    """Get drug names from user input."""
    print("\n=== Drug Interaction Checker ===")
    drug1 = input("Enter the first drug name: ").strip()
    drug2 = input("Enter the second drug name: ").strip()
    return drug1, drug2

def format_prediction(prediction: str, probability: float) -> str:
    """Format the prediction result for display."""
    result = prediction.upper()
    prob_percent = probability * 100
    return f"Prediction: {result} (confidence: {prob_percent:.1f}%)"

def main():
    try:
        # Check if model exists
        check_model_exists()
        print("Model found successfully!")
        
        while True:
            try:
                # Get user input
                drug1, drug2 = get_user_input()

                # Check if both inputs are the same drug
                if drug1.lower() == drug2.lower():
                    print("\n" + "="*50)
                    print(f"You entered the same drug twice: {drug1}")
                    print("Result: They are the SAME drug, no interaction check needed.")
                    print("="*50 + "\n")
                else:
                    # Make prediction using the function from ddi_pipeline
                    prediction, probability = predict_interaction(drug1, drug2)
                    
                    # Display result
                    print("\n" + "="*50)
                    print(f"Checking interaction between: {drug1} and {drug2}")
                    print(format_prediction(prediction, probability))
                    print("="*50 + "\n")
                
                # Ask to continue
                if input("Check another pair? (y/n): ").lower() != 'y':
                    print("Goodbye!")
                    break
                    
            except Exception as e:
                print(f"\nError: {str(e)}")
                print("Please try again.\n")
                
    except Exception as e:
        print(f"Error: {str(e)}")
        print("Please make sure the model file exists and is valid.")

if __name__ == "__main__":
    main()
