import os

def test_analyze_vocabulary_logic():
    print("Testing analyze_vocabulary prompt logic...")
    
    with open('backend/ai_service.py', 'r') as f:
        content = f.read()
        missing = []
        if 'normal' not in content: missing.append('normal')
        if 'attention' not in content: missing.append('attention')
        if 'punctuation' not in content: missing.append('punctuation')
        
        if not missing:
            print("SUCCESS: New prompt keywords found in ai_service.py")
        else:
            print(f"FAILURE: Keywords missing: {missing}")
            
    # Verify reading_service logic for saving
    with open('backend/reading_service.py', 'r') as f:
        rs_content = f.read()
        if 'p.translation = json.dumps' in rs_content and 'p.syntax = json.dumps' in rs_content:
             print("SUCCESS: JSON dumping assignment found in reading_service.py")
        else:
             print("FAILURE: Saving logic seemingly missing in reading_service.py")

    # Verify frontend Token interface
    with open('frontend/src/components/reading/ParagraphBlock.tsx', 'r') as f:
        fe_content = f.read()
        if "type: 'normal' | 'attention' | 'punctuation'" in fe_content:
             print("SUCCESS: Frontend Token interface updated")
        else:
             print("FAILURE: Frontend Token interface NOT updated correctly")

if __name__ == "__main__":
    test_analyze_vocabulary_logic()
