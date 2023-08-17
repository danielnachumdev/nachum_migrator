import sys
from sys import argv
from utils import get_directories, directory_exists
from gp_wrapper import GooglePhotos
from progress_bar_pool import ProgressBarPool, MockProgressBar
from utils import ERROR, INFO, WARNING
from local_album import LocalAlbum
from tqdm import tqdm

INDEX_FILE_NAME = "index.html"
HR_FOLDER_NAME = "hrimages"
IMAGE_PAGES = "imagepages"


def main() -> None:
    if len(argv) == 2:
        base_folder = argv[1]
        if not directory_exists(base_folder):
            print(f"{ERROR}Can't find directory {base_folder}")
            exit(1)
    else:
        if not len(argv) == 1:
            print(
                f"{ERROR}Wrong usage. Please supply a path to a directory or none at all")
        print(f"{WARNING}No argument supplied. using CWD instead")
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
    l_album = LocalAlbum(
        gp,
        base_folder,
        p,
        INDEX_FILE_NAME,
        HR_FOLDER_NAME,
        IMAGE_PAGES
    )
    l_album.upload()
    print("View album at: ", l_album.album.productUrl)

    # p.bars[1].reset()
    # p.bars[2].update()


if __name__ == "__main__":
    main()
