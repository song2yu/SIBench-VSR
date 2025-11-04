import os
import glob
import csv

task_dict = {
    'Geometric-Reasoning':{
        'number':252,
        'score':0.0
    },
    'Spatial-Relation':{
        'number':460,
        'score':0.0
    },
    'Temporal-Appearance-Order':{
        'number':11,
        'score':0.0
    },
    'multi-view-reasoning':{
        'number':943,
        'score':0.0
    },
    'relative-distance':{
        'number':676,
        'score':0.0
    },
    'Camera-Pose':{
        'number':344,
        'score':0.0
    },
    'Object-Shape':{
        'number':130,
        'score':0.0
    },
    'Spatial-Compatibility':{
        'number':214,
        'score':0.0
    },
    'Occlusion':{
        'number':500,
        'score':0.0
    },
    'Spatial-Imagination':{
        'number':400,
        'score':0.0
    },
    'Counting':{
        'number':238,
        'score':0.0
    },
    'Existence':{
        'number':40,
        'score':0.0
    },
    'Spatial-Grid':{
        'number':400,
        'score':0.0
    },
    'Maze-Navigation':{
        'number':400,
        'score':0.0
    },
    'Trajectory-Description':{
        'number':78,
        'score':0.0
    },
    'Reach-Prediction':{
        'number':40,
        'score':0.0
    },
    'Situational-QA':{
        'number':897,
        'score':0.0
    },
    'Coordinate-Conversion':{
        'number':800,
        'score':0.0
    },
    'Object-Localization':{
        'number':321,
        'score':0.0
    },
    'Route-Planning':{
        'number':59,
        'score':0.0
    },
    'Height':{
        'number':600,
        'score':0.0
    },
    'Object-Size-Estimation':{
        'number':468,
        'score':0.0
    },
    'Velocity-Acceleration':{
        'number':595,
        'score':0.0
    }
}

groups = {
    'basic_perception':['Object-Shape', 'Counting', 'Existence', 'Reach-Prediction', 'Height', 'Object-Size-Estimation', 'Occlusion'
    ],
    'spatial_understanding':['Geometric-Reasoning', 'Spatial-Relation', 'Temporal-Appearance-Order', 'multi-view-reasoning', 'relative-distance', 'Camera-Pose', 
    'Spatial-Compatibility', 'Spatial-Imagination', 'Spatial-Grid', 'Trajectory-Description',  'Situational-QA',
    'Coordinate-Conversion', 'Object-Localization', 'Velocity-Acceleration'
    ],
    'planning':['Route-Planning', 'Maze-Navigation'
    ]
}

def check_and_read_csv(directory_path, expected_count=23):
    """
    Retrieves all CSV files in the specified directory, checks the count,
    and if it matches, reads and prints their contents.

    :param directory_path: The target folder path to search in
    :param expected_count: The expected number of CSV files
    """
    
    # 1. Construct the file search pattern
    # os.path.join ensures the path is constructed correctly for any OS
    search_pattern = os.path.join(directory_path, "*.csv")
    
    # 2. Retrieve all matching CSV files
    # glob.glob returns a list of full paths for all matching files
    csv_files = glob.glob(search_pattern)
    
    # 3. Check the file count
    actual_count = len(csv_files)
    
    if actual_count != expected_count:
        # 4. If the count doesn't match, print an error and raise an exception
        error_message = f"File count mismatch. Expected: {expected_count}, Found: {actual_count}"
        print(f"Error: {error_message}")
        # Raise a ValueError to interrupt the program
        raise ValueError(error_message)
    
    # 5. If the count matches, proceed
    print(f"File count matched: Found {actual_count} CSV files.")
    print("--- Starting to read files ---")
    
    # 6. Read and print the elements of each CSV file in sequence
    overall = 0.0
    model_name = directory_path.split('/')[-1]
    for file_path in csv_files:
        # os.path.basename extracts the filename from the full path
        file_name = os.path.basename(file_path)
        task_name = '-'.join(file_name.replace(model_name, 'model').split('.')[0].split('_')[1:-1])
        try:
            # 'r' means read mode, encoding='utf-8' is a safe choice
            with open(file_path, mode='r', encoding='utf-8') as f:
                # Create a CSV reader object
                reader = csv.reader(f)
                next(reader) 
                score = float(next(reader)[1])
                task_dict[task_name]['score'] = score
                overall += task_dict[task_name]['number'] * score
                # Iterate over each row in the CSV file
                # task_dict[task_name] = score

                    
        except FileNotFoundError:
            print(f"  Error: File {file_name} was not found (it may have been moved or deleted).")
        except Exception as e:
            print(f"  An error occurred while reading {file_name}: {e}") 

    for level in ['basic_perception', 'spatial_understanding', 'planning']:
        score_level, number_level = 0.0, 0.0
        for task in groups[level]:
            score_level += task_dict[task]['number'] * task_dict[task]['score']
            number_level += task_dict[task]['number']
        print(f'{level}:{score_level/number_level}')
    print(f'Overall:{overall/8866.0}')

# --- Script execution entry point ---
if __name__ == "__main__":
    
    # The folder path you want to search
    target_directory = "outputs/output_folder" 
    try:
        # Call the main function
        check_and_read_csv(target_directory)
        
    except ValueError as e:
        # Catch the "file count mismatch" error we raised ourselves
        print(f"Script stopped.")
    except FileNotFoundError:
        # Catch a common error: if the target directory itself doesn't exist
        print(f"Error: The target directory was not found: {target_directory}")
    except Exception as e:
        # Catch any other unexpected errors
        print(f"An unexpected error occurred: {e}")
