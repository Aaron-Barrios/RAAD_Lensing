import csv
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from pathlib import Path

# Paths
root = Path(__file__).resolve().parents[3]
simple_dir = Path(__file__).resolve().parents[1]
manifest = simple_dir / "Training Data" / "output" / "dataset_manifest.csv"
output_csv = Path(__file__).resolve().parent / "pytorch_output.csv"

# Read the manifest
with open(manifest, newline="") as file:
    rows = list(csv.DictReader(file))

# Get the unique clean images
clean_images = sorted(set(row["clean_image_path"] for row in rows))

# Shuffle clean images reproducibly
rng = np.random.default_rng(42)
rng.shuffle(clean_images)

# Split by clean image, not degraded image
n = len(clean_images)

train_images = set(clean_images[:int(0.7 * n)])
val_images = set(clean_images[int(0.7 * n):int(0.85 * n)])
test_images = set(clean_images[int(0.85 * n):])

train_rows = [row for row in rows if row["clean_image_path"] in train_images]
val_rows = [row for row in rows if row["clean_image_path"] in val_images]
test_rows = [row for row in rows if row["clean_image_path"] in test_images]


# PyTorch Dataset
class BlackHoleDataset(Dataset):

    def __init__(self, rows):
        self.rows = rows

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        row = self.rows[index]

        # Load noisy and clean images
        with np.load(root / row["noisy_image_path"]) as data:
            noisy = data["image"].astype(np.float32)

        with np.load(root / row["clean_image_path"]) as data:
            clean = data["image"].astype(np.float32)

        # Convert to PyTorch tensors
        noisy = torch.from_numpy(noisy).unsqueeze(0)
        clean = torch.from_numpy(clean).unsqueeze(0)

        spin = torch.tensor(float(row["spin"]), dtype=torch.float32)
        inclination = torch.tensor(float(row["inclination_deg"]), dtype=torch.float32)

        return noisy, clean, spin, inclination


# Create DataLoaders
train_loader = DataLoader(
    BlackHoleDataset(train_rows),
    batch_size=16,
    shuffle=True
)

val_loader = DataLoader(
    BlackHoleDataset(val_rows),
    batch_size=16,
    shuffle=False
)

test_loader = DataLoader(
    BlackHoleDataset(test_rows),
    batch_size=16,
    shuffle=False
)

# Check the results
noisy, clean, spin, inclination = next(iter(train_loader))

output_rows = [
    ("Training pairs", len(train_rows)),
    ("Validation pairs", len(val_rows)),
    ("Test pairs", len(test_rows)),
    ("Noisy images", noisy.shape),
    ("Clean images", clean.shape),
    ("Spin", spin.shape),
    ("Inclination", inclination.shape),
]

for name, value in output_rows:
    print(f"{name}: {value}")

with output_csv.open("w", newline="") as file:
    writer = csv.writer(file, lineterminator="\n")
    writer.writerow(["output", "value"])
    writer.writerows(output_rows)

print("Output CSV:", output_csv)