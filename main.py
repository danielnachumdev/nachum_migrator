import sys
from sys import argv
from utils import get_directories, directory_exists
from gp_wrapper import GooglePhotos
from progress_bar_pool import ProgressBarPool, MockProgressBar
from utils import ERROR, INFO
from local_album import LocalAlbum
from tqdm import tqdm

INDEX_FILE_NAME = "index.html"
HR_FOLDER_NAME = "hrimages"
IMAGE_PAGES = "imagepages"


def main() -> None:
    if not len(argv) == 2:
        print(f"{ERROR}wrong usage, instead: python {__file__} PATH_TO_DIR")
        exit(1)
    base_folder = argv[1]
    if not directory_exists(base_folder):
        print(f"{Warning}Can't find directory {base_folder}. Using CWD instead")
        base_folder = "./"
    folder_names = get_directories(base_folder)
    p = ProgressBarPool(
        tqdm if sys.stdout.isatty() else MockProgressBar,
        2,
        global_options=dict(
        ),
        individual_options=[
            dict(
                desc="Uploading",
                leave=False,
            ),
            dict(
                desc="MediaItems",
                # leave=False
            ),
            # dict(
            #     desc="Albums",
            #     total=len(folder_names)
            # )
        ]
    )
    p.write(f"{INFO}Initializing GooglePhotos")
    gp = GooglePhotos()
    # for album_folder in folder_names:
    LocalAlbum(
        gp,
        base_folder,
        p,
        INDEX_FILE_NAME,
        HR_FOLDER_NAME,
        IMAGE_PAGES
    ).upload()
    # p.bars[1].reset()
    # p.bars[2].update()


if __name__ == "__main__":
    main()
