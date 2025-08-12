import os
from pathlib import Path


def rename_headers_files():
    """
    Rename all 'all_headers_2.json' files to 'all_headers_dict_2.json'
    in the results directory structure.
    """
    # Get the script directory (base directory)
    results_dir = Path("results_remote")

    if not results_dir.exists():
        print(f"✗ Results directory not found: {results_dir}")
        return

    renamed_count = 0

    # Walk through all directories and subdirectories in results/
    for root, dirs, files in os.walk(results_dir):
        root_path = Path(root)

        # Check if 'all_headers_2.json' exists in current directory
        old_file = root_path / "all_headers_2.json"
        new_file = root_path / "all_headers_dict_2.json"

        if old_file.exists():
            try:
                # Check if target file already exists
                if new_file.exists():
                    print(f"⚠️  Target file already exists, skipping: {new_file}")
                    continue

                # Rename the file
                old_file.rename(new_file)
                print(f"✓ Renamed: {old_file} -> {new_file}")
                renamed_count += 1

            except Exception as e:
                print(f"✗ Error renaming {old_file}: {e}")

    print(f"\n📊 Summary:")
    print(f"   Files renamed: {renamed_count}")

    if renamed_count == 0:
        print("   No 'all_headers_2.json' files found to rename.")


if __name__ == "__main__":
    rename_headers_files()