from sys import argv
from danielutils import get_directories


def main() -> None:
    base_folder = argv[1]
    for album_folder in get_directories(base_folder):
        print(album_folder)


if __name__ == "__main__":
    main()
