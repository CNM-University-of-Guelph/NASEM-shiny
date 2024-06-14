import pickle
with open('/Users/dave/Downloads/~NASEM_simulation-2024-06-10.NDsession', 'rb') as f:
            pkl_dict = pickle.load(f)
 
pkl_dict['FeedLibrary']


# pkl_dict.pop('FeedLibrary')
pkl_dict.pop("ModelOutput")
# Path to save the pickle file
# file_path = './dev/pkl_no_lib.NDsession'
file_path = './dev/pkl_no_ModelOutput.NDsession'

import os
#  os.makedirs(os.path.dirname(file_path), exist_ok=True)

# Open the file in write-binary mode and dump the dictionary
with open(file_path, 'wb') as file:
    pickle.dump(pkl_dict, file)

if os.path.exists(file_path):
    print(f"Pickle file saved successfully to {file_path}")
else:
    print("Failed to save the pickle file.")