from huggingface_hub import snapshot_download

# your path
LOCAL_DIR = "./"
DATASET_NAME = "Two-hot/SIBench"

# download the dataset
local_path = snapshot_download(
    repo_id=DATASET_NAME, 
    repo_type="dataset", 
    local_dir=LOCAL_DIR
)

print(f"✅ download to: {local_path}")
